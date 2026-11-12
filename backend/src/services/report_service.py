import csv,io
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from ..models.review import IncidentReview
from ..models.run import ChangeRun
from ..models.report import Report

exclusion_labels={"stopped":"停机","zero_output":"零产量","missing_measurement":"缺测"}

def create(db,body):
 review=db.get(IncidentReview,body.review_id)
 if review is None or review.state!="approved":raise HTTPException(409,"报告必须关联已批准的复核")
 existing=db.scalar(select(Report).where(Report.review_id==body.review_id))
 if existing:return existing
 run=db.get(ChangeRun,review.run_id);row=Report(id=str(uuid4()),review_id=review.id,title=body.title,snapshot={"result":run.result,"action":review.action,"reviewer":review.reviewer});db.add(row);db.commit();return row

def _cell(value):return "" if value is None else value

def export(row):
 result=row.snapshot["result"];out=io.StringIO();writer=csv.writer(out)
 writer.writerow(["timestamp","kwh","output_kg","intensity_kwh_per_kg","block_index","analyzed","segment_median","robust_score","anomaly","excluded_reason"])
 for obs in result["observations"]:
  writer.writerow([obs["timestamp"],_cell(obs.get("kwh")),_cell(obs.get("output_kg")),obs.get("intensity"),obs.get("block_index",0) if "block_index" in obs else 0,obs.get("analyzed",True) if "analyzed" in obs else True,_cell(obs.get("baseline")),_cell(obs.get("score")),obs.get("anomaly",False),""])
 for item in result.get("excluded",[]):
  writer.writerow([item["timestamp"],"","","","","","","","",exclusion_labels.get(item["reason"],item["reason"])])
 return "﻿"+out.getvalue()
