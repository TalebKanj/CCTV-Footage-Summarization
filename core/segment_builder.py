
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

    final_segments = []

    for start_idx, end_idx in raw_segments:

        expanded_start = max(0, start_idx - pre_event_frames)
        expanded_end = end_idx + post_event_frames

        if total_frames is not None:
            expanded_end = min(total_frames - 1, expanded_end)

        final_segments.append({
            "start_frame": expanded_start,
            "end_frame": expanded_end,
            "start_time": round(expanded_start / fps, 3),
            "end_time": round(expanded_end / fps, 3),
            "duration_sec": round((expanded_end - expanded_start + 1) / fps, 3),
            "trigger_start_frame": start_idx,
            "trigger_end_frame": end_idx
        })

    return final_segments
