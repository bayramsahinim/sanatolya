import base64,json,sys,urllib.request
def gen(prompt,out,ref=None,model="gemini-3-pro-image",aspect="9:16"):
    parts=[]
    if ref:
        for r in ref: parts.append({"inlineData":{"mimeType":"image/png","data":base64.b64encode(open(r,'rb').read()).decode()}})
    parts.append({"text":prompt})
    body={"contents":[{"parts":parts}],"generationConfig":{"responseModalities":["IMAGE"],"imageConfig":{"aspectRatio":aspect,"imageSize":"2K"}}}
    req=urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",data=json.dumps(body).encode(),headers={"Content-Type":"application/json","x-goog-api-key":"dummy"})
    d=json.load(urllib.request.urlopen(req,timeout=600))
    for p in d["candidates"][0]["content"]["parts"]:
        if "inlineData" in p:
            open(out,'wb').write(base64.b64decode(p["inlineData"]["data"])); print("saved",out); return
    print(json.dumps(d)[:500])
if __name__=="__main__":
    gen(sys.argv[1],sys.argv[2],sys.argv[3:] or None)
