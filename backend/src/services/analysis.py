from .blocks import split_blocks
from .change_points import detect
from .robust_scores import score

def run_analysis(observations,excluded,config):
 """按观测间隔分块后逐块独立计算；短块保留观测但不分析，不拖垮其他块。"""
 max_gap=float(config.get("max_gap_hours",6.));min_segment=int(config["min_segment"])
 blocks=split_blocks(observations,max_gap)
 all_values=[r["intensity"] for r in observations]
 for obs in observations:obs.update(block_index=None,analyzed=True,score=None,baseline=None,anomaly=False)
 segments=[];change_indices=[];total_sse=0.;robust_blocks=[];analyzed_count=0;unanalyzed_count=0
 analyzed_blocks=0;unanalyzed_blocks=0
 for block in blocks:
  a,b=block["start_index"],block["end_index"]
  for i in range(a,b):observations[i]["block_index"]=block["block_index"]
  if block["count"]<min_segment:
   block["analyzed"]=False
   reason=f"有效观测{block['count']}条，少于最小段长{min_segment}条，不参与分段与异常计算"
   block["reason"]=reason
   for i in range(a,b):observations[i]["analyzed"]=False
   unanalyzed_count+=b-a;unanalyzed_blocks+=1
   continue
  local_values=all_values[a:b]
  changes=detect(local_values,float(config["penalty"]),min_segment)
  for seg in changes["segments"]:
   seg=dict(seg)
   seg["block_index"]=block["block_index"]
   seg["start_index"]+=a;seg["end_index"]+=a
   seg["start_at"]=observations[seg["start_index"]]["timestamp"]
   seg["end_at"]=observations[seg["end_index"]-1]["timestamp"]
   total_sse+=seg["sse"];segments.append(seg)
  change_indices.extend(a+i for i in changes["change_indices"])
  robust=score(local_values,changes["segments"],float(config["anomaly_threshold"]),float(config["noise_floor"]))
  for detail in robust["segments"]:
   detail["start_index"]+=a;detail["end_index"]+=a;detail["block_index"]=block["block_index"]
  robust_blocks.append({"block_index":block["block_index"],**{k:v for k,v in robust.items() if k!="segments"},"segments":robust["segments"]})
  anomaly_local=set(robust["anomaly_indices"])
  for offset,i in enumerate(range(a,b)):
   observations[i].update(score=robust["scores"][offset],baseline=robust["baselines"][offset],anomaly=offset in anomaly_local)
  analyzed_count+=b-a;analyzed_blocks+=1
 if analyzed_blocks==0:
  raise ValueError(f"所有{len(blocks)}个分块均短于最小段长{min_segment}条，无可分析工况块；观测已保留但未计算")
 anomaly_count=sum(1 for obs in observations if obs["anomaly"])
 changes={"change_indices":change_indices,"segments":segments,"objective":None,"penalty":float(config["penalty"]),"min_segment":min_segment,"max_gap_hours":max_gap,"total_sse":float(total_sse),"criterion":"sum(within-segment SSE) + penalty × number of change points，分块独立计算，分段不跨观测缺口","block_rule":f"相邻有效观测间隔严格大于{max_gap:g}小时则分块，等于门槛不分块"}
 robust={"threshold":float(config["anomaly_threshold"]),"noise_floor":float(config["noise_floor"]),"blocks":robust_blocks,"formula":"abs(residual - segment median residual) / max(1.4826 × MAD, noise_floor)，分段与异常基线不跨缺口"}
 result_config={**config,"max_gap_hours":max_gap}
 return {"observations":observations,"excluded":excluded,"changes":changes,"robust":robust,"blocks":blocks,"valid_count":len(observations),"excluded_count":len(excluded),"analyzed_observation_count":analyzed_count,"unanalyzed_observation_count":unanalyzed_count,"analyzed_block_count":analyzed_blocks,"unanalyzed_block_count":unanalyzed_blocks,"anomaly_count":anomaly_count,"config":result_config}
