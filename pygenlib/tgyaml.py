class TgYaml:
    def __init__(self):
        self.tg_info = []

    def record_tg(self, st, tg, pts, public=False, c=None):
        self.tg_info.append({
            "subtask": st,
            "tg_id": tg,
            "points": pts,
            "public": public,
            "comment": c
        })

    def _tg_interval(self, tg_list):
        mn_tg = min(tg_list, key=lambda tg: tg["tg_id"])
        mx_tg = max(tg_list, key=lambda tg: tg["tg_id"])
        return f"[{mn_tg['tg_id']}, {mx_tg['tg_id']}]"

    def export(self, yaml_path="task.yaml"):
        f = open(yaml_path, "w")
        f.write("""
tests_groups:
    - groups: 0
      points: 0
      public: true
      subtask: 0
      comment: Piemēri
    """)
        flush_tg = lambda tgs: f.write(f"""
    - groups: {self._tg_interval(tgs)}
      points: {tgs[0]["points"]}
      public: {tgs[0]["public"]}
      subtask: {tgs[0]["subtask"]}
{"      comment: " + tgs[0]["comment"] if tgs[0]["comment"] else ""}""")
        tg_buffer = []
        for tg in self.tg_info:
            if len(tg_buffer) == 0:
                tg_buffer.append(tg)
            elif tg_buffer[-1]["subtask"] == tg["subtask"] and \
                tg_buffer[-1]["public"] == tg["public"] and \
                tg_buffer[-1]["points"] == tg["points"]:
                tg_buffer.append(tg)
            else:
                flush_tg(tg_buffer)
                tg_buffer = [tg]
        if len(tg_buffer) > 0:
            flush_tg(tg_buffer)