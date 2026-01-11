from app import create_app

app = create_app()

if __name__ == '__main__':
    # Threaded=True ensures Flask handles multiple requests (and our background threads) correctly
    app.run(debug=True, port=5000, threaded=True)
  
