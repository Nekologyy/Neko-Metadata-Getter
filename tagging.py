import os

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4, MP4Cover
    from mutagen.flac import FLAC, Picture
    from mutagen.id3 import (
        ID3, TIT2, TPE1, TALB, TPE2, TCON, TDRC, TRCK, APIC, ID3NoHeaderError
    )
except ModuleNotFoundError as error:
    raise ModuleNotFoundError(
        
    ) from error
 
FIELDS = ["title", "artist", "album", "albumartist", "genre", "year", "tracknumber"]
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".mp4", ".flac")
 
 
def detect_format(path):
    
    audio = MutagenFile(path)
    if audio is None:
        raise ValueError("Unsupported audio format or file is not an audio file.")
    return audio
 
 
def read_existing_tags(path):
   
    tags = {}
    try:
        easy = MutagenFile(path, easy=True)
        if easy and easy.tags:
            for field in FIELDS:
                easy_key = "date" if field == "year" else field
                if easy_key in easy.tags:
                    tags[field] = easy.tags[easy_key][0]
    except Exception:
        pass
    return tags
 
 
def guess_from_filename(path):
    
    name = os.path.splitext(os.path.basename(path))[0]
    if " - " in name:
        artist, title = name.split(" - ", 1)
        return artist.strip(), title.strip()
    return "", name.strip()
 
 
def write_tags(path, audio, final, cover_bytes):
    if isinstance(audio, MP3):
        try:
            id3 = ID3(path)
        except ID3NoHeaderError:
            id3 = ID3()
        id3["TIT2"] = TIT2(encoding=3, text=final["title"])
        id3["TPE1"] = TPE1(encoding=3, text=final["artist"])
        id3["TALB"] = TALB(encoding=3, text=final["album"])
        id3["TPE2"] = TPE2(encoding=3, text=final["albumartist"])
        id3["TCON"] = TCON(encoding=3, text=final["genre"])
        id3["TDRC"] = TDRC(encoding=3, text=final["year"])
        id3["TRCK"] = TRCK(encoding=3, text=str(final["tracknumber"]))
        if cover_bytes:
            id3["APIC"] = APIC(
                encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_bytes
            )
        id3.save(path, v2_version=3)
 
    elif isinstance(audio, MP4):
        tag = MP4(path)
        tag["\xa9nam"] = [final["title"]]
        tag["\xa9ART"] = [final["artist"]]
        tag["\xa9alb"] = [final["album"]]
        tag["aART"] = [final["albumartist"]]
        tag["\xa9gen"] = [final["genre"]]
        tag["\xa9day"] = [final["year"]]
        if final["tracknumber"]:
            try:
                tag["trkn"] = [(int(final["tracknumber"]), 0)]
            except ValueError:
                pass
        if cover_bytes:
            tag["covr"] = [MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_JPEG)]
        tag.save()
 
    elif isinstance(audio, FLAC):
        audio["title"] = final["title"]
        audio["artist"] = final["artist"]
        audio["album"] = final["album"]
        audio["albumartist"] = final["albumartist"]
        audio["genre"] = final["genre"]
        audio["date"] = final["year"]
        audio["tracknumber"] = str(final["tracknumber"])
        if cover_bytes:
            pic = Picture()
            pic.data = cover_bytes
            pic.type = 3
            pic.mime = "image/jpeg"
            audio.clear_pictures()
            audio.add_picture(pic)
        audio.save()
 
    else:
        raise ValueError(f"Unsupported/unhandled format: {type(audio).__name__}")
