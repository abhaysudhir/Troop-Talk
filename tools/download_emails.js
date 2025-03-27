// Configuration variables
var CONFIG = {
  groupEmail: 'MissionPeakTroop125@googlegroups.com',
  startDate: new Date('2024-01-01'), // Set your desired start date here
  endDate: new Date('2024-12-31')    // Set your desired end date here
};

function saveEmailsAsEML() {
  var groupEmail = CONFIG.groupEmail;
  
  // Format dates for Gmail search query
  var startDateStr = Utilities.formatDate(CONFIG.startDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
  var endDateStr = Utilities.formatDate(CONFIG.endDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
  
  // Create search query with date range
  var searchQuery = 'to:' + groupEmail + ' after:' + startDateStr + ' before:' + endDateStr;
  var threads = GmailApp.search(searchQuery);
  
  // Create folder with date range in name
  var folderName = 'MissionPeakTroop125_Emails_' + 
                   Utilities.formatDate(CONFIG.startDate, Session.getScriptTimeZone(), "yyyy_MM") + '_' +
                   Utilities.formatDate(CONFIG.endDate, Session.getScriptTimeZone(), "yyyy_MM");
  var folder = DriveApp.createFolder(folderName);

  for (var i = 0; i < threads.length; i++) {
    var threadMessages = threads[i].getMessages();
    for (var j = 0; j < threadMessages.length; j++) {
      var message = threadMessages[j];
      var messageDate = message.getDate();
      
      // Check if the email is within the specified date range
      if (messageDate >= CONFIG.startDate && messageDate <= CONFIG.endDate) {
        // Convert each message to EML format
        var rawMessage = message.getRawContent();
        var fileName = 'Message_' + messageDate.toISOString() + '.eml';

        // Save the email as an EML file in Google Drive
        folder.createFile(fileName, rawMessage, MimeType.PLAIN_TEXT);
      }
    }
  }
}