import os
import cv2
import numpy as np
import easyocr
from PIL import Image, ImageDraw, ImageFont

IMAGE_DIR = './images'
VIS_DIR = './vis_images'
os.makedirs(VIS_DIR, exist_ok=True)

def vis_and_save(img_path, results, vis_dir):
    img_cv2 = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img_cv2 is None:
        print(f'无法读取图片: {img_path}')
        return
    for r in results:
        # r[0]是box，坐标格式与test1.py一致
        try:
            box = np.array(r[0], dtype=np.int32)
            cv2.polylines(img_cv2, [box], isClosed=True, color=(0, 200, 0), thickness=2)
        except Exception as e:
            continue
    img_pil = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    try:
        font_path = "C:/Windows/Fonts/simhei.ttf"
        font = ImageFont.truetype(font_path, 18)
    except Exception as e:
        font = ImageFont.load_default()
    for r in results:
        try:
            x_min = min([point[0] for point in r[0]])
            y_min = min([point[1] for point in r[0]])
            conf = float(r[2]) if len(r) >= 3 and r[2] is not None else None
            label = f"{r[1]} ({conf if conf is not None else '-'})"
            draw.text((x_min, max(0, y_min - 5)), label, font=font, fill=(255,0,0))
        except Exception as e:
            continue
    img_res = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    out_name = os.path.splitext(os.path.basename(img_path))[0] + '_vis.jpg'
    out_path = os.path.join(vis_dir, out_name)
    _, buf = cv2.imencode('.jpg', img_res)
    buf.tofile(out_path)

if __name__ == "__main__":
    image_paths = [os.path.join(IMAGE_DIR, fname) for fname in os.listdir(IMAGE_DIR) if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'))]
    image_paths.sort()
    if not image_paths:
        print("images 文件夹下没有图片！")
        exit()
    print(f"共{len(image_paths)}张图片，开始极简OCR输出所有识别内容...\n")
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

    for img_path in image_paths:
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        # 图像可选二值化，必要时注释掉下一行
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 25, 15)
        results = reader.readtext(img, detail=1, paragraph=False, rotation_info=[0, 90, 180, 270])
        print(f"\n== {img_path} ==")
        if not results:
            print("[无任何返回内容]")
        for r in results:
            # 不做任何过滤，全输出
            try:
                conf = float(r[2]) if len(r) >= 3 and r[2] is not None else None
            except:
                conf = None
            print(f"[conf={conf}] {r[1]}")
        vis_and_save(img_path, results, VIS_DIR)
    print(f"可视化图片已全部生成，保存在: {VIS_DIR}/")
