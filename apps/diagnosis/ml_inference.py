import os
import json
from functools import lru_cache

import numpy as np
from django.conf import settings

from .analyzer import generate_real_gradcam

MODEL_DIR = os.path.join(str(settings.BASE_DIR), 'apps', 'diagnosis', 'ml')
IMG_SIZE = 224

CLASS_LABELS_FA = {
    'NonDemented': 'سالم (CN)',
    'VeryMildDemented': 'اختلال بسیار خفیف (MCI)',
    'MildDemented': 'اختلال خفیف (AD اولیه)',
    'ModerateDemented': 'آلزایمر (AD)',
}
CLASS_COLORS = {
    'NonDemented': '#22c55e',
    'VeryMildDemented': '#f59e0b',
    'MildDemented': '#f97316',
    'ModerateDemented': '#ef4444',
}
RESULT_MAP = {
    'NonDemented': 'CN',
    'VeryMildDemented': 'MCI',
    'MildDemented': 'AD',
    'ModerateDemented': 'AD',
}
REGION_NAMES_FA = ['هیپوکامپوس راست', 'هیپوکامپوس چپ', 'قشر آنتورینال راست', 'قشر آنتورینال چپ']

RECOMMENDATIONS = {
    'CN': (
        'بر اساس تحلیل تصویر MRI، الگوی قابل توجهی از آتروفی مغزی مشاهده نشد. '
        'ادامه پیگیری‌های دوره‌ای سالانه توصیه می‌شود.'
    ),
    'MCI': (
        'الگویی سازگار با اختلال خفیف شناختی (MCI) مشاهده شده است. '
        'توصیه می‌شود ارزیابی‌های تکمیلی هر ۶ ماه انجام و با متخصص مغز و اعصاب مشورت شود.'
    ),
    'AD': (
        'الگوی آتروفی قابل توجهی سازگار با آلزایمر مشاهده شده است. '
        'مراجعه فوری به متخصص مغز و اعصاب برای ارزیابی بالینی کامل توصیه می‌شود.'
    ),
}


@lru_cache(maxsize=1)
def _load_model():
    import tensorflow as tf

    model_path = os.path.join(MODEL_DIR, 'alzheimer_model.keras')
    labels_path = os.path.join(MODEL_DIR, 'class_names.json')
    if not os.path.exists(model_path) or not os.path.exists(labels_path):
        raise FileNotFoundError(
            f"Model files not found in {MODEL_DIR}. Train "
            "notebooks/alzheimer_model_training.ipynb and place "
            "alzheimer_model.keras + class_names.json there."
        )

    model = tf.keras.models.load_model(model_path)
    with open(labels_path, encoding='utf-8') as f:
        class_names = json.load(f)
    return model, class_names


def _preprocess(image_path):
    import tensorflow as tf

    img = tf.keras.utils.load_img(image_path, target_size=(IMG_SIZE, IMG_SIZE))
    arr = tf.keras.utils.img_to_array(img)
    return np.expand_dims(arr, axis=0)


def _gradcam_heatmap(model, img_array, base_layer_name='mobilenetv2_base', last_conv_name='Conv_1'):
    import tensorflow as tf

    base_model = model.get_layer(base_layer_name)
    conv_layer = base_model.get_layer(last_conv_name)
    grad_model = tf.keras.models.Model(model.inputs, [conv_layer.output, model.output])

    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(img_array)
        class_idx = tf.argmax(preds[0])
        class_channel = preds[:, class_idx]

    grads = tape.gradient(class_channel, conv_out)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_out = conv_out[0]
    heatmap = tf.reduce_sum(conv_out * pooled_grads, axis=-1)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    return heatmap.numpy()


def analyze_mri_real(image_path):
    """Run the trained model + real Grad-CAM and return a dict with the exact
    shape DEMO_RESULT / templates/dashboard/result.html expect."""
    model, class_names = _load_model()
    img_array = _preprocess(image_path)
    preds = model.predict(img_array, verbose=0)[0]

    probabilities = [
        {
            'key': name,
            'label': CLASS_LABELS_FA.get(name, name),
            'value': round(float(preds[i]) * 100, 1),
            'color': CLASS_COLORS.get(name, '#64748b'),
        }
        for i, name in enumerate(class_names)
    ]

    top_idx = int(np.argmax(preds))
    top_class = class_names[top_idx]
    confidence = round(float(preds[top_idx]) * 100, 1)
    result = RESULT_MAP.get(top_class, 'PENDING')
    result_label = CLASS_LABELS_FA.get(top_class, top_class)

    heatmap = _gradcam_heatmap(model, img_array)
    heatmap_url, atrophy_values = generate_real_gradcam(image_path, heatmap)

    healthy_prob = next((p['value'] for p in probabilities if p['key'] == 'NonDemented'), 0)
    risk_score = max(0, min(100, int(round(100 - healthy_prob))))

    regions = [
        {
            'name': REGION_NAMES_FA[i],
            'atrophy': v,
            'severity': 'شدید' if v >= 60 else 'متوسط' if v >= 35 else 'خفیف' if v >= 20 else 'طبیعی',
            'level': 'warning' if v >= 35 else 'info' if v >= 20 else 'success',
        }
        for i, v in enumerate(atrophy_values)
    ]

    return {
        'result': result,
        'result_label': result_label,
        'confidence': confidence,
        'probabilities': probabilities,
        'regions': regions,
        'risk_score': risk_score,
        'recommendation': RECOMMENDATIONS.get(result, ''),
        'heatmap_url': heatmap_url,
    }
