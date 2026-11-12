from .readings import parse_time

def split_blocks(observations,max_gap_hours):
 """按相邻有效观测的时间间隔分块：间隔严格大于上限才切开，等于门槛保留同块。"""
 blocks=[]
 if not observations:return blocks
 start=0;gap_before=None
 for i in range(1,len(observations)+1):
  gap=None;cut=False
  if i<len(observations):
   gap=(parse_time(observations[i]["timestamp"])-parse_time(observations[i-1]["timestamp"])).total_seconds()/3600.
   cut=gap>max_gap_hours
  if cut or i==len(observations):
   blocks.append({"block_index":len(blocks),"start_index":start,"end_index":i,"count":i-start,"start_at":observations[start]["timestamp"],"end_at":observations[i-1]["timestamp"],"gap_before_hours":None if gap_before is None else round(gap_before,3),"analyzed":True,"reason":""})
   if cut:start=i;gap_before=gap
 return blocks
