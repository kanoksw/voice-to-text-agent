import json
from validator import validate_data, build_message
from agent_utils import merge_data
from pipeline_full import speech_to_text, extract_fields
from romanize import romanize_person

def run_agent_loop(audio_paths: list[str]) -> dict:
    """
    Run multi-turn agent loop using a list of audio paths in order.
    Example: ["input.wav", "input2.wav", "input3.wav"]
    """
    # รอบแรก
    transcript = speech_to_text(audio_paths[0])
    data = extract_fields(transcript, expected_fields=[])

    status, missing = validate_data(data)
    if status == "complete":
        return {"status": "complete", "data": romanize_person(data)}

    # รอบต่อ ๆ ไป
    for i in range(1, len(audio_paths)):
        transcript_i = speech_to_text(audio_paths[i])
        new_data = extract_fields(transcript_i, expected_fields=missing)

        data = merge_data(data, new_data, missing)

        status, missing = validate_data(data)
        if status == "complete":
            return {"status": "complete", "data": romanize_person(data)}

    # ถ้ายังไม่ complete หลังหมดไฟล์เสียงที่ให้มา
    return {
        "status": "incomplete",
        "missing_fields": missing,
        "message": build_message(missing),
        "data_partial": data
    }