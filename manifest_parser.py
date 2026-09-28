import json
from pathlib import Path


def load_manifest(path: str) -> dict:
    """Đọc file manifest JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_prompt_from_manifest(manifest: dict) -> str:
    """Tự động sinh prompt chi tiết từ manifest"""
    image = manifest.get("image", {})
    landmarks = manifest.get("landmarks", [])
    camera = manifest.get("camera", {})

    width = image.get("width", 0)
    height = image.get("height", 0)
    mean_rgb = image.get("mean_rgb", [])

    # Mô tả màu sắc tổng thể
    color_desc = ""
    if mean_rgb and len(mean_rgb) >= 3:
        r, g, b = mean_rgb[:3]
        if r > g and r > b:
            tone = "warm"
        elif b > r and b > g:
            tone = "cool"
        else:
            tone = "neutral"
        color_desc = f"The overall color tone is {tone} with averaged RGB values. "

    # Mô tả camera / bố cục
    fov = camera.get("fov_guess_deg", 58)
    composition = camera.get("composition_target", "")
    projection = camera.get("projection", "perspective")

    camera_desc = (
        f"Shot with a {projection} camera at approximately {fov} degrees field of view. "
    )
    if composition:
        camera_desc += f"Composition flows from {composition}. "

    # Mô tả các landmarks
    landmark_parts = []
    foreground_parts = []
    background_parts = []

    for lm in landmarks:
        name = lm.get("name", "").replace("_", " ")
        kind = lm.get("kind", "")
        depth = lm.get("depth", 0.5)
        cx = lm.get("cx", 0.5)
        cy = lm.get("cy", 0.5)

        position_words = []
        if cx < 0.4:
            position_words.append("left")
        elif cx > 0.6:
            position_words.append("right")
        else:
            position_words.append("center")

        if cy < 0.35:
            position_words.append("top")
        elif cy > 0.65:
            position_words.append("bottom/foreground")
        else:
            position_words.append("middle")

        desc = f"a {name} ({kind}) positioned at the {' '.join(position_words)}"
        if depth < 0.4:
            foreground_parts.append(desc + " in the foreground")
        elif depth > 0.7:
            background_parts.append(desc + " in the background")
        else:
            landmark_parts.append(desc + " in the midground")

    scene_desc = ""
    if foreground_parts:
        scene_desc += "In the foreground: " + ", ".join(foreground_parts) + ". "
    if landmark_parts:
        scene_desc += "In the midground: " + ", ".join(landmark_parts) + ". "
    if background_parts:
        scene_desc += "In the background: " + ", ".join(background_parts) + ". "

    prompt = (
        "Cinematic video scene. "
        + color_desc
        + camera_desc
        + scene_desc
        + "Smooth camera movement, high detail, professional lighting, realistic atmosphere."
    )

    return prompt


def generate_prompt_from_manifest_file(manifest_path: str) -> str:
    """Tiện ích: đọc file manifest và sinh prompt"""
    manifest = load_manifest(manifest_path)
    return generate_prompt_from_manifest(manifest)


if __name__ == "__main__":
    # Test
    test = {
        "image": {"mean_rgb": [187.3, 172.8, 170.2]},
        "camera": {
            "projection": "perspective",
            "fov_guess_deg": 58,
            "composition_target": "foreground bridge -> plaza -> stairs -> palace"
        },
        "landmarks": [
            {"name": "main_palace", "kind": "palace", "cx": 0.52, "cy": 0.25, "depth": 0.78},
            {"name": "grand_stairs", "kind": "stairs", "cx": 0.52, "cy": 0.45, "depth": 0.66},
            {"name": "circular_plaza", "kind": "plaza", "cx": 0.53, "cy": 0.56, "depth": 0.55},
            {"name": "foreground_bridge", "kind": "bridge", "cx": 0.3, "cy": 0.78, "depth": 0.22},
        ]
    }
    print(generate_prompt_from_manifest(test))
