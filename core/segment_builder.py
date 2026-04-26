
def build_segments(
    selected_frames,
    fps,
    merge_gap_sec=1.0,
    pre_event_sec=2.0,
    post_event_sec=2.0,
    total_frames=None
):

    if not selected_frames:
        return []

    sorted_frames = sorted(selected_frames, key=lambda x: x["frame_index"])

    selected_indices = [frame["frame_index"] for frame in sorted_frames]

    merge_gap_frames = int(merge_gap_sec * fps)
    pre_event_frames = int(pre_event_sec * fps)
    post_event_frames = int(post_event_sec * fps)

    raw_segments = []

    segment_start = selected_indices[0]
    segment_end = selected_indices[0]

    for current_index in selected_indices[1:]:

        if current_index - segment_end <= merge_gap_frames:
            segment_end = current_index
        else:
            raw_segments.append((segment_start, segment_end))
            segment_start = current_index
            segment_end = current_index

    raw_segments.append((segment_start, segment_end))

    merged_final_segments = []
    
    for start_idx, end_idx in raw_segments:

        expanded_start = max(0, start_idx - pre_event_frames)
        expanded_end = end_idx + post_event_frames

        if total_frames is not None:
            expanded_end = min(total_frames - 1, expanded_end)

        new_segment = {
            "start_frame": expanded_start,
            "end_frame": expanded_end,
            "start_time": round(expanded_start / fps, 3),
            "end_time": round(expanded_end / fps, 3),
            "duration_sec": round((expanded_end - expanded_start + 1) / fps, 3),
            "trigger_start_frame": start_idx,
            "trigger_end_frame": end_idx
        }
        
        if not merged_final_segments:
            merged_final_segments.append(new_segment)
        else:
            last_segment = merged_final_segments[-1]
            if new_segment["start_frame"] <= last_segment["end_frame"]:
                # Overlap! Merge them.
                last_segment["end_frame"] = max(last_segment["end_frame"], new_segment["end_frame"])
                last_segment["end_time"] = round(last_segment["end_frame"] / fps, 3)
                last_segment["duration_sec"] = round((last_segment["end_frame"] - last_segment["start_frame"] + 1) / fps, 3)
                last_segment["trigger_end_frame"] = max(last_segment["trigger_end_frame"], new_segment["trigger_end_frame"])
            else:
                merged_final_segments.append(new_segment)
    # Filter out segments less than 1.0 seconds
    final_segments = [seg for seg in merged_final_segments if seg["duration_sec"] >= 1.0]

    return final_segments
