# Dota Ban Pick Tool User Console

The Dota Ban Pick User Console is a React-based application designed to assist Dota 2 players in to design and store their hero pools. 

## Key Features

- Hero Pool Management: Easily design and store customized hero pools.
- Strategic Planning: Facilitate the planning of hero picks and bans.
- Performance Tracking: Monitor and analyze your heroes' performance over time.
- Integration with Dota 2 API: Fetch the latest hero stats and data.
- User-Friendly Interface: Designed for accessibility and ease of use.

## Setup Local Environment 

To get started with the Dota Ban Pick Tool User Console:

1. Clone the repository
2. ```bash
    curl -fsSL https://deb.nodesource.com/setup_21.x | sudo -E bash - &&\
    sudo apt-get install -y nodejs
    npm create vite@latest
    npm create vite@latest yourapp -- --template react-ts
    cd yourapp
    npm install
    npm install antd react-redux react-router-dom redux sass reset-css # can also add them to package
    npm i -D @types/node
    npm run dev
    ```

## Technologies and Frameworks

- React.js for the frontend
- Redux for state management
- MongoDB for database management
- Integration with the Dota 2 API
