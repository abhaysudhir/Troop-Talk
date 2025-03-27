// Configuration variables
var CONFIG = {
  groupEmail: 'MissionPeakTroop125@googlegroups.com',
  startDate: new Date('2025-03-09'), // Set your desired start date here
  endDate: new Date('2025-03-26'),   // Set your desired end date here
  debug: true                        // Enable/disable debugging
};

function saveEmailsAsEML() {
  var startTime = new Date();
  Logger.log("Script started at: " + startTime);
  
  var groupEmail = CONFIG.groupEmail;
  Logger.log("Target email group: " + groupEmail);
  
  // Format dates for Gmail search query
  var startDateStr = Utilities.formatDate(CONFIG.startDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
  var endDateStr = Utilities.formatDate(CONFIG.endDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
  Logger.log("Date range: " + startDateStr + " to " + endDateStr);
  
  // Create search query with date range
  var searchQuery = 'to:' + groupEmail + ' after:' + startDateStr + ' before:' + endDateStr;
  Logger.log("Search query: " + searchQuery);
  
  // Search for email threads
  Logger.log("Searching for email threads...");
  var threads = GmailApp.search(searchQuery);
  Logger.log("Found " + threads.length + " threads");
  
  // Create folder with date range in name
  var folderName = 'MissionPeakTroop125_Emails_' + 
                   Utilities.formatDate(CONFIG.startDate, Session.getScriptTimeZone(), "yyyy_MM") + '_' +
                   Utilities.formatDate(CONFIG.endDate, Session.getScriptTimeZone(), "yyyy_MM");
  Logger.log("Creating folder: " + folderName);
  var folder = DriveApp.createFolder(folderName);
  Logger.log("Folder created with ID: " + folder.getId());

  var emailsProcessed = 0;
  var emailsSaved = 0;
  var emailsSkipped = 0;
  
  for (var i = 0; i < threads.length; i++) {
    if (CONFIG.debug && i % 10 === 0) {
      Logger.log("Processing thread " + (i+1) + " of " + threads.length);
    }
    
    var threadMessages = threads[i].getMessages();
    Logger.log("Thread #" + (i+1) + " contains " + threadMessages.length + " messages");
    
    for (var j = 0; j < threadMessages.length; j++) {
      emailsProcessed++;
      var message = threadMessages[j];
      var messageDate = message.getDate();
      var subject = message.getSubject();
      
      // Check if the email is within the specified date range
      if (messageDate >= CONFIG.startDate && messageDate <= CONFIG.endDate) {
        try {
          // Convert each message to EML format
          var rawMessage = message.getRawContent();
          var fileName = 'Message_' + messageDate.toISOString() + '.eml';
          Logger.log("Saving email: " + subject + " (" + fileName + ")");
          
          // Save the email as an EML file in Google Drive
          folder.createFile(fileName, rawMessage, MimeType.PLAIN_TEXT);
          emailsSaved++;
          
          if (CONFIG.debug && emailsSaved % 10 === 0) {
            Logger.log("Progress: Saved " + emailsSaved + " emails so far");
          }
        } catch (error) {
          Logger.log("ERROR saving email: " + subject);
          Logger.log("Error details: " + error.toString());
        }
      } else {
        emailsSkipped++;
        if (CONFIG.debug) {
          Logger.log("Skipping email outside date range: " + subject + " (Date: " + messageDate + ")");
        }
      }
    }
  }
  
  var endTime = new Date();
  var executionTime = (endTime - startTime) / 1000;
  
  // Log summary statistics
  Logger.log("====== EXECUTION SUMMARY ======");
  Logger.log("Total threads found: " + threads.length);
  Logger.log("Total emails processed: " + emailsProcessed);
  Logger.log("Emails saved: " + emailsSaved);
  Logger.log("Emails skipped: " + emailsSkipped);
  Logger.log("Execution time: " + executionTime + " seconds");
  Logger.log("Output folder: " + folderName + " (ID: " + folder.getId() + ")");
  Logger.log("==============================");
  
  return {
    threadsFound: threads.length,
    emailsProcessed: emailsProcessed,
    emailsSaved: emailsSaved,
    emailsSkipped: emailsSkipped,
    executionTime: executionTime,
    folderName: folderName,
    folderId: folder.getId()
  };
}