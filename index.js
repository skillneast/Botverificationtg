const functions = require("firebase-functions");
const admin = require("firebase-admin");
const cors = require("cors")({ origin: true });

admin.initializeApp();
// YAHAN FIRESTORE KI JAGAH REALTIME DATABASE USE KAR RAHE HAIN
const rtdb = admin.database();

exports.verifyToken = functions.https.onRequest((req, res) => {
    cors(req, res, async () => {
        if (req.method !== "POST") {
            return res.status(405).json({ success: false, error: "Method Not Allowed" });
        }

        const { token } = req.body;
        if (!token) {
            return res.status(400).json({ success: false, error: "Token is required." });
        }

        try {
            const usersRef = rtdb.ref('users');
            // RTDB mein query aise hoti hai. Hum token se user ko dhoondh rahe hain.
            const snapshot = await usersRef.orderByChild('token').equalTo(token).once('value');

            if (!snapshot.exists()) {
                return res.status(404).json({ success: false, error: "Invalid Token." });
            }

            // User ka data nikalo
            const userId = Object.keys(snapshot.val())[0];
            const userData = snapshot.val()[userId];

            // --- MANUAL EXPIRY CHECK ---
            // Ab ka time seconds mein
            const currentTimeSeconds = Math.floor(Date.now() / 1000);
            
            // Agar token ka expiry time ab ke time se kam hai, to token expire ho chuka hai
            if (userData.expiry_timestamp < currentTimeSeconds) {
                return res.status(401).json({ success: false, error: "Token has expired." });
            }

            // Check karo ki token pehle se use to nahi hua
            if (userData.used) {
                return res.status(403).json({ success: false, error: "This token has already been used." });
            }

            // Token ko 'used' mark kar do
            await rtdb.ref(`users/${userId}`).update({ used: true });

            return res.status(200).json({ success: true, message: "Access granted." });

        } catch (error) {
            console.error("Verification Error:", error);
            return res.status(500).json({ success: false, error: "Internal server error." });
        }
    });
});
