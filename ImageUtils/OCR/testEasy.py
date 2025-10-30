import os
import glob
import json
import cv2
import numpy as np
import easyocr
from PIL import Image, ImageDraw, ImageFont

# 配置输入输出路径
IMAGE_DIR = './images'
OUT_JSON = './ocr_result.json'
VIS_DIR = './vis_images'

os.makedirs(VIS_DIR, exist_ok=True)

def is_image_file(filename):
    return filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'))

def vis_and_save(img_path, results, vis_dir):
    img_cv2 = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img_cv2 is None:
        print(f'无法读取图片: {img_path}')
        return
    for r in results:
        box = np.array(r['box'], dtype=np.int32)
        cv2.polylines(img_cv2, [box], isClosed=True, color=(0, 200, 0), thickness=2)
    # 用PIL绘制中文
    img_pil = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font_path = "C:/Windows/Fonts/simhei.ttf"  # 确保存在此字体
        font = ImageFont.truetype(font_path, 18)
    except Exception as e:
        print(f"加载字体失败: {e}")
        font = ImageFont.load_default()
    for r in results:
        x_min = min([point[0] for point in r['box']])
        y_min = min([point[1] for point in r['box']])
        label = f"{r['text']} ({r['confidence']:.2f})"
        draw.text((x_min, max(0, y_min - 5)), label, font=font, fill=(255,0,0))
    img_res = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    out_name = os.path.splitext(os.path.basename(img_path))[0] + '_vis.jpg'
    out_path = os.path.join(vis_dir, out_name)
    _, buf = cv2.imencode('.jpg', img_res)
    buf.tofile(out_path)

def preprocess_image(img_cv2):
    gray = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2GRAY)
    # 自适应二值化
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 25, 15)
    return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

def main():
    # 统一批量找图像
    image_paths = [os.path.join(IMAGE_DIR, fname) for fname in os.listdir(IMAGE_DIR) if is_image_file(fname)]
    image_paths.sort()
    if not image_paths:
        print("images 文件夹下没有图片！")
        return

    print(f"共{len(image_paths)}张图片，开始识别...\n")
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    all_results = {}
    for img_path in image_paths:
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        img = preprocess_image(img)  # 添加图像预处理
        results = reader.readtext(img, detail=1, paragraph=False, rotation_info=[0, 90, 180, 270])
        items = []
        for r in results:
            if len(r) >= 3 and r[2] is not None and float(r[2]) >= 0.1:
                items.append({
                    'box': [[float(x), float(y)] for x, y in r[0]],  # 四点坐标
                    'text': r[1],
                    'confidence': float(r[2])
                })
        all_results[img_path] = items
        print(f"\n== {img_path} ==")
        for it in items:
            print(f"[{it['confidence']:.2f}] {it['text']}  box={it['box']}")
        vis_and_save(img_path, items, VIS_DIR)

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {OUT_JSON}")
    print(f"可视化图片保存在: {VIS_DIR}/")

if __name__ == "__main__":
    main()