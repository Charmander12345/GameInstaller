import requests
import msal
import base64
import os

# Azure AD App-Details
CLIENT_ID = "12be65dc-7e2b-4167-82dd-2ce4a0c3ecce"
TENANT_ID = "e26f77c3-1dee-42ba-ae48-7ba44efd4dea"

AUTHORITY = f"https://login.microsoftonline.com/consumers"
SCOPES = ["https://graph.microsoft.com/.default"]
ONEDRIVE = "https://1drv.ms/f/s!Arhj3sKOJ8rPg6Vzms_xkBTb2Wqvtg?e=aODw5B"

def authenticate():
    """
    Authentifiziert die App und gibt ein Zugriffstoken zurück.
    """
    app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
    
    # Anforderung des Tokens mit interaktiver Authentifizierung (Benutzerauthentifizierung)
    result = app.acquire_token_interactive(scopes=SCOPES)
    
    if "access_token" not in result:
        raise Exception("Fehler bei der Authentifizierung: ", result.get("error_description"))
    
    return result["access_token"]

def download_shared_folder_personal(share_link, access_token, output_dir="./downloads"):
    # Share-Link in Share-ID umwandeln (Dieser Schritt bleibt gleich)
    share_id = base64.urlsafe_b64encode(share_link.encode("utf-8")).decode("utf-8").strip("=")
    
    # Zugriff auf die freigegebenen Elemente auf deinem persönlichen OneDrive
    url = f"https://graph.microsoft.com/v1.0/shares/{share_id}/driveItem/children"

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        os.makedirs(output_dir, exist_ok=True)
        for item in response.json().get("value", []):
            file_name = item["name"]
            
            # Überprüfen, ob es sich um eine Datei handelt
            if "@microsoft.graph.downloadUrl" in item:
                download_url = item["@microsoft.graph.downloadUrl"]
                print(f"Herunterladen: {file_name}")
                
                # Datei herunterladen
                with requests.get(download_url, stream=True) as file_response:
                    with open(os.path.join(output_dir, file_name), "wb") as file:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            if chunk:
                                file.write(chunk)
            else:
                print(f"Ordner gefunden, überspringe: {file_name}")
    else:
        print(f"Fehler beim Abrufen der Ordnerdaten: {response.status_code}, {response.text}")

if __name__ == "__main__":
    try:
        # Authentifizierung
        token = authenticate()
        print("Authentifizierung erfolgreich.")

        # Ordnerinhalt abrufen
        download_shared_folder_personal(ONEDRIVE, token)
    except Exception as e:
        print("Fehler:", e)
