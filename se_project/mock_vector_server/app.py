from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI()

@app.get('/search')
def search(query: str):
    return {'results': []}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)