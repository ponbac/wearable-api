# PoE Stash Explorer - Backend
FastAPI application used as a backend for [PoE Stash Explorer](https://github.com/ponbac/poe-currency). Handles making API requests to various API:s (e.g. poe.ninja and GGG) while also caching relevant non/slowly-changing content for faster responses.

This application also handles user authentication including providing expiring JWT tokens to the clients, while blocking certain requests if the client does not provide a valid token.

User data (e.g. usernames, hashed passwords, friends, etc.) is stored using Firebase Firestore with the Firebase Credentials being hidden in environment variables.

The connection to the official private Path of Exile API is established following the guidelines at [Path of Exile - Developer Docs](https://www.pathofexile.com/developer/docs/index) using OAuth2. This requires steps such as generating a valid PoE authorization link with a unique state, then handling the response from PoE and matching the state with the correct user for whom the initial authorization link was generated. If the authentication is successful, the access- and request tokens are saved in Firestore.

# API Docs
You can try the API out here: [api.backman.app](https://api.backman.app/docs). This is deployed using Heroku's app containers.

# TODO
* Refactor more! (begin by moving user authentication into its own router, the same applies for the image grabbing)
* Bug with the PoE OAuth2 state where it sometimes does not get correctly added to the temporary dict!