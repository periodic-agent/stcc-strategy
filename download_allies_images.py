import urllib.request
import os

images = {
    "allies_1.jpg": "https://cf.geekdo-images.com/vA-AitC02U7noPJeOu6Mfw__large/img/Vs3RXNsyYdNL5_90cLRjUrEDXGs=/fit-in/1024x1024/filters:no_upscale():strip_icc()/pic8963426.jpg",
    "allies_2.jpg": "https://cf.geekdo-images.com/wReRJhcqKWAcFbovxnRRJw__large/img/MMVHwZHZZ8S38ugyqvSO-Gs9peQ=/fit-in/1024x1024/filters:no_upscale():strip_icc()/pic8963427.jpg",
    "allies_3.jpg": "https://cf.geekdo-images.com/JR3-yriKL3aaV5CWZ9kAFw__large/img/0cjTr3-jCso0H-r7xh2GnCDEcRc=/fit-in/1024x1024/filters:no_upscale():strip_icc()/pic8963428.jpg",
    "allies_4.jpg": "https://cf.geekdo-images.com/z7rAj8nExAFXRJT8iG2FaQ__large/img/ww6hCdPT0ULCYxqEvf7wTtcIRN0=/fit-in/1024x1024/filters:no_upscale():strip_icc()/pic8963429.jpg",
}

out_dir = "allies_images"
os.makedirs(out_dir, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}

for filename, url in images.items():
    req = urllib.request.Request(url, headers=headers)
    out_path = os.path.join(out_dir, filename)
    with urllib.request.urlopen(req) as response, open(out_path, "wb") as f:
        f.write(response.read())
    print(f"Downloaded {filename}")

print(f"\nDone. Images saved to ./{out_dir}/")
