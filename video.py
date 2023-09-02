from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl import types, functions
import asyncio,random,os,time
from PIL import Image
import mimetypes
import io
import json
import cv2
import numpy as np
from io import BytesIO

cliId = 12345
cliHash = "hashhsahhashhashhsahhash"
client = TelegramClient("myuser", cliId, cliHash, receive_updates=False)

index = None
indexMsg = None
me = None


async def newIndex():
    start_index = {
        "supportedTags": [],
        "photo": [],
        "video": []
    }

    json_data = json.dumps(start_index)
    data_bytes = json_data.encode('utf-8')


    msg = await client.send_file("me", file=data_bytes, caption="index2.tg",attributes=[types.DocumentAttributeFilename("index2.tg")])

    pin_msg = await client.pin_message("me", msg)
    return msg

async def uploadIndex():
    global index

    json_str = json.dumps(index)
    json_bytes = json_str.encode('utf-8')

    await client.edit_message("me", indexMsg.id, file = json_bytes)
    pass


async def getIndex():
    global index,indexMsg,me
    chat = 'me'
    me = await client.get_me()

    pinnedList = await client.get_messages(chat, None, filter=types.InputMessagesFilterPinned)
    for i in pinnedList:
        if i.media and type(i.media) == types.MessageMediaDocument and i.message == 'index2.tg':
            indexMsg = i
            break


    if not indexMsg:
        ioo = await client.get_me()
        if ioo:
            await newIndex()
            return (await getIndex())
    else:
        json_bytes = await indexMsg.download_media(file=bytes)
        json_str = json_bytes.decode('utf-8')
        index = json.loads(json_str) 
        return index

    

def generate_video_thumbnails(video_path,period = 10):
    cap = cv2.VideoCapture(video_path)

    frame_interval = period * int(cap.get(cv2.CAP_PROP_FPS)) 
    output_frame_size = (120, 70)
    rectangle_width = 120
    rectangle_height = 70

    frames = []

    frame_counter = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_counter += 1

        if frame_counter % frame_interval == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            #frame = cv2.resize(frame, output_frame_size)
            #frames.append(frame)


            frame_height, frame_width, _ = frame.shape
            new_height = int(rectangle_width * frame_height / frame_width)
            if new_height >= rectangle_height:
                target_height = rectangle_height
                target_width = int(rectangle_height * frame_width / frame_height)
            else:
                target_height = new_height
                target_width = rectangle_width

            resized_frame = cv2.resize(frame, (target_width, target_height), cv2.INTER_AREA)
            resized_frame = cv2.blur(resized_frame, (2, 2))
            black_rectangle = np.zeros((rectangle_height, rectangle_width, 3), dtype=np.uint8)

            x_offset = (rectangle_width - target_width) // 2
            y_offset = (rectangle_height - target_height) // 2

            black_rectangle[y_offset:y_offset+target_height, x_offset:x_offset+target_width] = resized_frame
            frames.append(black_rectangle)            
            

    num_frames = len(frames)
    composite_width = num_frames * output_frame_size[0]
    composite_image = np.zeros((output_frame_size[1], composite_width, 3), dtype=np.uint8)

    for i, frame in enumerate(frames):
        composite_image[:, i * output_frame_size[0]:(i + 1) * output_frame_size[0], :] = frame


    composite_image_pil = Image.fromarray(composite_image)
    image_bytes = BytesIO()
    composite_image_pil.save(image_bytes, format='PNG',quality=90)
    cap.release()
    return image_bytes.getvalue()


def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    orientation = 0 

    if width > height:
        orientation = 1

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = frame_count / fps

    cap.release()

    return orientation, video_duration



def get_video_preview_as_bytes(video_path, frame_num=0, target_resolution=(320, 320)):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, target_resolution)
        _, img_encoded = cv2.imencode(".jpg", frame)
        img_bytes = img_encoded.tobytes()
        cap.release()

        return img_bytes
    else:
        print("err")
        return None

async def main():
    async with client:
        await getIndex()

        for j in sorted([each for each in os.listdir("./video") if each.endswith('.mp4')] , key=lambda x: os.path.getsize(os.path.join("./video", x)) ):

            jj = "./video/"+j
            with open(jj,"rb") as f:
                no = abs(random.getrandbits(63))
                count = os.path.getsize(jj)//(512*1024) +1
                print(count)
                listo = []
                for i in range(count):
                    print(i," / ",count," - ", j)
                    if count > 20:
                        listo.append(asyncio.create_task(client(functions.upload.SaveBigFilePartRequest(no,i,count,f.read(512*1024)))))
                    else:
                        listo.append(asyncio.create_task(client(functions.upload.SaveFilePartRequest(no,i,f.read(512*1024)))))

                    if len(listo) > 25:
                        if not listo[0].done():
                            await listo[0]
                        del listo[0]
                    
                print("ok1")

                for i in listo:
                    await i
                print("OK2")

                if count > 20:
                    result = types.InputFileBig(
                        no,
                        count,
                        j
                    )
                else:
                    result = types.InputFile(
                        no,
                        count,
                        j,
                        ""
                    )


                ent = await client.get_entity("me")
                
                orientation, duration = get_video_info(jj)

                thumb = get_video_preview_as_bytes(jj,100 if duration < 15 else 300 )
                video_thumb = generate_video_thumbnails(jj, (3 if duration < 60 else (6 if duration < 60*5 else (9 if duration < 60*15 else 15) ) ))
                print("OK2.5")
                send_file = await client.send_file(ent, result, thumb=thumb, force_document=True, caption=j, silent=True)
                
                print("OK2.7")
                send_thumb_file = await client.send_file(ent, video_thumb, force_document=True, caption="sweep_"+j+".png", attributes=[types.DocumentAttributeFilename("sweep_"+j+".png")], silent=True)
                print("OK3")
                print("name: " + j)
                item = {
                    "mimeType" : mimetypes.guess_type(j, strict=False)[0],
                    "favorite": False,
                    "trashed": False,
                    "msgId": send_file.id,
                    "date": int(os.path.getctime(jj)),
                    "tags": [
                        #"notags"
                        eval(input('enter tags like ["tag1","tag2",...]: '))
                    ],
                    "label": j,
                    "orientation": orientation,
                    "chatId": me.id,
                    "size": os.path.getsize(jj),
                    "duration": str(int(duration)*1000),
                    "thumbnailMsgId": send_thumb_file.id
                }
                print(item)
                index["video"].append(item)
                print("OK4")

            os.remove(jj)    
            await uploadIndex()

        print("OK5")

asyncio.run(main())