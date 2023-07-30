from fastapi import FastAPI

app = FastAPI()

@app.get("/drive_link")
async def get_drive_link():
    # Replace this link with your desired Google Drive link
    drive_link = "https://drive.google.com/drive/folders/1TJnZ_dGDGlXBcaaxOs57oE1aeKf-dXfD"
    return {"drive_link": drive_link}
