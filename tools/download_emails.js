function saveEmailsAsEML() {
  var groupEmail = 'MissionPeakTroop125@googlegroups.com'; // Your group email
  var threads = GmailApp.search('to:' + groupEmail); // Searches all emails sent to the group
  var folder = DriveApp.createFolder('MissionPeakTroop125_Emails_2024_2025'); // Creates a folder in Google Drive to store the EML files

  for (var i = 0; i < threads.length; i++) {
    var threadMessages = threads[i].getMessages();
    for (var j = 0; j < threadMessages.length; j++) {
      var message = threadMessages[j];
      var messageDate = message.getDate(); // Get the date of the email
      
      // Check if the email is from 2024 or 2025
      if (messageDate.getFullYear() === 2024 || messageDate.getFullYear() === 2025) {
        // Convert each message to EML format
        var rawMessage = message.getRawContent();
        var fileName = 'Message_' + messageDate.toISOString() + '.eml'; // Name the file based on the date of the email

        // Save the email as an EML file in Google Drive
        folder.createFile(fileName, rawMessage, MimeType.PLAIN_TEXT);
      }
    }
  }
}