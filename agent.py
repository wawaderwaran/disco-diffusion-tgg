import subprocess
from time import sleep
from loguru import logger
import requests
import json
import argparse
import os
from dotenv import load_dotenv


def loop(args=None):
    DD_URL = args.dd_url
    DD_NAME = args.agent
    DD_IMAGES_OUT = args.images_out
    DD_CUDA_DEVICE = args.cuda_device
    POLL_INTERVAL = args.poll_interval

    url = f"{DD_URL}/takeorder/{DD_NAME}"
    run = True
    while run == True:
        connected = False
        try:
            logger.debug(f"🌎 Checking '{url}'")
            results = requests.get(url).json()
            if results["success"]:
                connected = True
                prompt = json.dumps({0: [results["details"]["text_prompt"]]})
                steps = results["details"]["steps"]
                uuid = results["details"]["uuid"]
                shape = results["details"]["shape"]
                model = results["details"]["model"]
                clip_guidance_scale = results["details"]["clip_guidance_scale"]
                cut_ic_pow = results["details"]["cut_ic_pow"]
                w_h = [1280, 768]
                RN101 = False
                RN50 = True
                RN50x16 = False
                RN50x4 = False
                RN50x64 = False
                ViTB16 = True
                ViTB32 = True
                ViTL14 = False
                ViTL14_336 = False

                if not clip_guidance_scale:
                    clip_guidance_scale = 1500

                if not cut_ic_pow:
                    cut_ic_pow = 1

                if not model:
                    model = "default"

                if model == "rn50x64":
                    RN50x64 = True
                    RN50 = False

                if model == "vitl14":
                    RN50 = False
                    ViTL14 = True

                if model == "vitl14x336":
                    RN50 = False
                    ViTL14_336 = True

                if not shape:
                    shape = "landcape"

                if shape == "landscape":
                    w_h = [1280, 768]
                if shape == "portrait":
                    w_h = [768, 1280]
                if shape == "square":
                    w_h = [1024, 1024]
                if shape == "pano":
                    w_h = [2048, 512]
                job = f"python disco.py --batch_name={uuid} --cuda_device={DD_CUDA_DEVICE} --n_batches=1 --images_out={DD_IMAGES_OUT} --steps={steps} --clip_guidance_scale={clip_guidance_scale} --cut_ic_pow={cut_ic_pow} --text_prompts"
                cmd = job.split(" ")
                cmd.append(f"{prompt}")
                cmd.append(f"--width_height")
                cmd.append(json.dumps(w_h))
                cmd.append(f"--RN101")
                cmd.append(str(RN101))
                cmd.append(f"--RN50")
                cmd.append(str(RN50))
                cmd.append(f"--RN50x4")
                cmd.append(str(RN50x4))
                cmd.append(f"--RN50x16")
                cmd.append(str(RN50x16))
                cmd.append(f"--RN50x64")
                cmd.append(str(RN50x64))
                cmd.append(f"--ViTB16")
                cmd.append(str(ViTB16))
                cmd.append(f"--ViTB32")
                cmd.append(str(ViTB32))
                cmd.append(f"--ViTL14")
                cmd.append(str(ViTL14))
                cmd.append(f"--ViTL14_336")
                cmd.append(str(ViTL14_336))
                print(cmd)
                logger.info(f"Running...:\n{job}")
                log = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("utf-8")
                logger.info(log)
                files = {"file": open(f"{DD_IMAGES_OUT}/{uuid}/{uuid}(0)_0.png", "rb")}
                values = {}
                r = requests.post(f"{DD_URL}/upload/{DD_NAME}/{uuid}", files=files, data=values)
            else:
                logger.error(f"Error: {results['message']}")
        except KeyboardInterrupt:
            logger.info("Exiting...")
            run = False
        except Exception as e:
            if connected:
                logger.error(f"Bad job detected.\n\n{e}")
                values = {"message": f"Job failed:\n\n{e}"}
                r = requests.post(f"{DD_URL}/reject/{DD_NAME}/{uuid}", data=values)
            else:
                logger.error(f"Error.  Check your DD_URL and if the DD app is running at that location.  Also check your own internet connectivity.  Exception:\n{e}")
        finally:
            logger.info(f"Sleeping for {POLL_INTERVAL} seconds...")
            sleep(POLL_INTERVAL)


def main():

    load_dotenv()
    parser = argparse.ArgumentParser(description="Disco Diffusion")
    parser.add_argument("--dd_url", help="Discord Bot http endpoint", required=False, default=os.getenv("DD_URL"))
    parser.add_argument("--agent", help="Your agent name", required=False, default=os.getenv("DD_NAME"))
    parser.add_argument("--images_out", help="Directory for render jobs", required=False, default=os.getenv("DD_IMAGES_OUT", "images_out"))
    parser.add_argument("--cuda_device", help="CUDA Device", required=False, default=os.getenv("DD_CUDA_DEVICE", "cuda:0"))
    parser.add_argument("--poll_interval", type=int, help="Polling interval between jobs", required=False, default=os.getenv("DD_POLL_INTERVAL", 5))
    args = parser.parse_args()
    loop(args)


if __name__ == "__main__":
    main()
