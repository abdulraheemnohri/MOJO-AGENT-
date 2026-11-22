import uvicorn
def main():uvicorn.run('mojo_agent.api:app',host='127.0.0.1',port=8766,reload=False)
if __name__=='__main__':main()
