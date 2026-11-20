"""
Disk Scheduling Algorithms: FCFS, SSTF, and SCAN (Elevator).
Calculates head movements, seek distances, seek sequences, and comparative metrics.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DiskSchedulingResult:
    algorithm: str
    initial_head: int
    requests: List[int]
    seek_sequence: List[int]  # List of visited tracks starting from initial_head
    step_seeks: List[int]     # Distance moved in each step
    total_seek_operations: int
    average_seek_distance: float
    total_cylinders: int = 200

    def step_table(self) -> List[Dict[str, Any]]:
        """Returns a list of dicts describing each movement step."""
        table = []
        for i in range(1, len(self.seek_sequence)):
            from_track = self.seek_sequence[i - 1]
            to_track = self.seek_sequence[i]
            dist = self.step_seeks[i - 1]
            table.append({
                "Step": i,
                "From Cylinder": from_track,
                "To Cylinder": to_track,
                "Seek Distance": dist,
                "Direction": "Inward (High)" if to_track > from_track else ("Outward (Low)" if to_track < from_track else "Same")
            })
        return table

    def summary_dict(self) -> Dict[str, Any]:
        return {
            "Algorithm": self.algorithm,
            "Initial Head": self.initial_head,
            "Total Requests": len(self.requests),
            "Total Head Movements": self.total_seek_operations,
            "Average Seek Distance": round(self.average_seek_distance, 2),
            "Final Head Position": self.seek_sequence[-1] if self.seek_sequence else self.initial_head
        }


def schedule_disk_fcfs(initial_head: int, requests: List[int], total_cylinders: int = 200) -> DiskSchedulingResult:
    """
    First-Come, First-Served (FCFS) Disk Scheduling.
    Services track requests in exact arrival sequence.
    """
    if not requests:
        return DiskSchedulingResult(
            algorithm="FCFS",
            initial_head=initial_head,
            requests=[],
            seek_sequence=[initial_head],
            step_seeks=[],
            total_seek_operations=0,
            average_seek_distance=0.0,
            total_cylinders=total_cylinders
        )

    seek_sequence = [initial_head] + list(requests)
    step_seeks = []
    total_seek = 0

    for i in range(1, len(seek_sequence)):
        dist = abs(seek_sequence[i] - seek_sequence[i - 1])
        step_seeks.append(dist)
        total_seek += dist

    avg_seek = total_seek / len(requests) if requests else 0.0

    return DiskSchedulingResult(
        algorithm="FCFS (First-Come First-Served)",
        initial_head=initial_head,
        requests=requests,
        seek_sequence=seek_sequence,
        step_seeks=step_seeks,
        total_seek_operations=total_seek,
        average_seek_distance=avg_seek,
        total_cylinders=total_cylinders
    )


def schedule_disk_sstf(initial_head: int, requests: List[int], total_cylinders: int = 200) -> DiskSchedulingResult:
    """
    Shortest Seek Time First (SSTF) Disk Scheduling.
    Always selects the pending request closest to current head position.
    """
    if not requests:
        return DiskSchedulingResult(
            algorithm="SSTF",
            initial_head=initial_head,
            requests=[],
            seek_sequence=[initial_head],
            step_seeks=[],
            total_seek_operations=0,
            average_seek_distance=0.0,
            total_cylinders=total_cylinders
        )

    pending = list(requests)
    curr_head = initial_head
    seek_sequence = [curr_head]
    step_seeks = []
    total_seek = 0

    while pending:
        # Find pending request with minimum distance to curr_head
        closest_idx = min(range(len(pending)), key=lambda i: abs(pending[i] - curr_head))
        closest_track = pending.pop(closest_idx)

        dist = abs(closest_track - curr_head)
        step_seeks.append(dist)
        total_seek += dist

        curr_head = closest_track
        seek_sequence.append(curr_head)

    avg_seek = total_seek / len(requests) if requests else 0.0

    return DiskSchedulingResult(
        algorithm="SSTF (Shortest Seek Time First)",
        initial_head=initial_head,
        requests=requests,
        seek_sequence=seek_sequence,
        step_seeks=step_seeks,
        total_seek_operations=total_seek,
        average_seek_distance=avg_seek,
        total_cylinders=total_cylinders
    )


def schedule_disk_scan(
    initial_head: int,
    requests: List[int],
    total_cylinders: int = 200,
    direction: str = "high"
) -> DiskSchedulingResult:
    """
    SCAN (Elevator) Disk Scheduling.
    Head moves in one direction servicing requests until reaching the cylinder boundary,
    then reverses direction servicing remaining requests.
    """
    if not requests:
        return DiskSchedulingResult(
            algorithm="SCAN",
            initial_head=initial_head,
            requests=[],
            seek_sequence=[initial_head],
            step_seeks=[],
            total_seek_operations=0,
            average_seek_distance=0.0,
            total_cylinders=total_cylinders
        )

    max_track = total_cylinders - 1
    left = sorted([r for r in requests if r < initial_head])
    right = sorted([r for r in requests if r >= initial_head])

    seek_sequence = [initial_head]

    if direction.lower() == "high":
        # Service towards max cylinder, then reverse
        for r in right:
            seek_sequence.append(r)
        if left:
            if seek_sequence[-1] != max_track:
                seek_sequence.append(max_track)
            for r in reversed(left):
                seek_sequence.append(r)
    else:
        # Service towards 0, then reverse
        for r in reversed(left):
            seek_sequence.append(r)
        if right:
            if seek_sequence[-1] != 0:
                seek_sequence.append(0)
            for r in right:
                seek_sequence.append(r)

    step_seeks = []
    total_seek = 0
    for i in range(1, len(seek_sequence)):
        dist = abs(seek_sequence[i] - seek_sequence[i - 1])
        step_seeks.append(dist)
        total_seek += dist

    avg_seek = total_seek / len(requests) if requests else 0.0

    return DiskSchedulingResult(
        algorithm=f"SCAN (Elevator - {direction.capitalize()})",
        initial_head=initial_head,
        requests=requests,
        seek_sequence=seek_sequence,
        step_seeks=step_seeks,
        total_seek_operations=total_seek,
        average_seek_distance=avg_seek,
        total_cylinders=total_cylinders
    )
