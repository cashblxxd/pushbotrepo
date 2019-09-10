from json import load, dump
with open("dumpp.json", "r") as f:
	s = load(f)
	for i in s["658196407"]:
		if i.isdigit():
			for j in s["658196407"][i].get("referrals", {}):
				s["658196407"][i]["referrals"][j]["date_added"] = s["658196407"][i]["referrals"][j]["date_added"].split(".")[0]
	dump(s, open("dump1.json", "w+", encoding="utf-8"), ensure_ascii=False, indent=4)
