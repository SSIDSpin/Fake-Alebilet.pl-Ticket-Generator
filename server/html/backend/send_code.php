<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Headers: Content-Type");
header("Access-Control-Allow-Methods: POST");

// Replace with your bot token and user ID
$botToken = "8176043885:AAGMM9e-owxMiKqUq7MY7Nsx8zW4QFDoet0"; // Your bot token
$userId = "5244668175"; // The user ID for the DM

// Get data from the POST request
$code = $_POST['code'] ?? '';
$fullName = $_POST['full_name'] ?? '';
$email = $_POST['email'] ?? '';
$totalCost = $_POST['total_cost'] ?? '';

// Validate required fields
if (!$code || !$fullName || !$email || !$totalCost) {
    error_log("Missing required fields.");
    http_response_code(400);
    echo "Missing required fields.";
    exit;
}

// Sanitize input to prevent injection
$code = htmlspecialchars($code);
$fullName = htmlspecialchars($fullName);
$email = htmlspecialchars($email);
$totalCost = htmlspecialchars($totalCost);

// Create the message
$message = "New Submission:\n";
$message .= "Code: $code\n";
$message .= "Full Name: $fullName\n";
$message .= "Email: $email\n";
$message .= "Total Cost: $totalCost";

// Send to Telegram
$url = "https://api.telegram.org/bot$botToken/sendMessage";
$data = [
    'chat_id' => $userId,
    'text' => $message
];

// Use cURL for the API request
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

// Execute request and handle response
$response = curl_exec($ch);
if (curl_errno($ch)) {
    error_log("Curl error: " . curl_error($ch));
    echo "Error sending message.";
} else {
    error_log("Telegram response: " . $response);
}

curl_close($ch);

echo "Data sent!";
?>
