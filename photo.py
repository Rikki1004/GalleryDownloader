from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession
from telethon.tl import types, functions
import asyncio,random,os,time
from PIL import Image
import mimetypes
import io
import json

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

    

def determine_image_orientation(image_path):
    try:
        with Image.open(image_path) as img:
            exif = img._getexif()

            if exif is not None:
                orientation = exif.get(274)
                if orientation is not None:
                    exif_orientation_codes = {
                        1: 0,
                        3: 0,
                        6: 1,
                        8: 1
                    }

                    if orientation in exif_orientation_codes:
                        return exif_orientation_codes[orientation]

            width, height = img.size
            if width == height:
                return 2  
            elif width > height:
                return 1  
            else:
                return 0 
    except Exception as e:
        print("err:", e)
        return 0 

    

def crop_to_square(image_path):
    img = Image.open(image_path)

    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img.thumbnail((320,320))
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


async def main():
    async with client:
        counter = 1
        await getIndex()
        ent = await client.get_entity("me")

        if ent != None:
            for j in [each for each in os.listdir("./photo") if each.endswith('.jpg')]:
                if counter%10 == 0:
                    await uploadIndex()
                    print("uploaded index")
                counter+=1
                
                jj = "./photo/"+j
                with open(jj,"rb") as f:
                    
                    thumb = crop_to_square(jj)
                    send_file = await client.send_file(ent, f, thumb=thumb, force_document=True, caption=j, silent=True)
                    item = {
                        "mimeType" : mimetypes.guess_type(j, strict=False)[0],
                        "favorite": False,
                        "trashed": False,
                        "msgId": send_file.id,
                        "date": int(os.path.getctime(jj)),#int(time.time()),
                        "tags": [
                                    #"notags"
                                    eval(input('enter tags like ["tag1","tag2",...]: '))
                            ],
                        "label": j,
                        "orientation": determine_image_orientation(jj),
                        "chatId": me.id,
                        "size": os.path.getsize(jj),
                    }
                    print(item)
                    index["photo"].append(item)

                    print("OK1")
                os.remove(jj) #images are deleted from this folder in order not to upload them again in case of a failure

            print("ok2")   
            await uploadIndex()
            
        print("ok3")

asyncio.run(main())