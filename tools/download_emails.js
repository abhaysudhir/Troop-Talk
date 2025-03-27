// Configuration variables
var CONFIG = {
  groupEmail: 'MissionPeakTroop125@googlegroups.com',
  startDate: new Date('2025-03-09'), // Set your desired start date here
  endDate: new Date('2025-03-26'),   // Set your desired end date here
  debug: true,                      // Enable/disable debugging
  chunkSizeDays: 1,                 // Break down searches into chunks of days to avoid Gmail API limits
  maxThreadsPerQuery: 500           // Gmail typically limits results to around 500-1000 threads
};

function saveEmailsAsEML() {
  var startTime = new Date();
  Logger.log("Script started at: " + startTime);
  
  var groupEmail = CONFIG.groupEmail;
  Logger.log("Target email group: " + groupEmail);
  Logger.log("Date range: " + CONFIG.startDate.toISOString() + " to " + CONFIG.endDate.toISOString());
  
  // Create folder with date range in name
  var folderName = 'MissionPeakTroop125_Emails_' + 
                   Utilities.formatDate(CONFIG.startDate, Session.getScriptTimeZone(), "yyyy_MM_dd") + '_to_' +
                   Utilities.formatDate(CONFIG.endDate, Session.getScriptTimeZone(), "yyyy_MM_dd");
  Logger.log("Creating folder: " + folderName);
  var folder = DriveApp.createFolder(folderName);
  Logger.log("Folder created with ID: " + folder.getId());

  var emailsProcessed = 0;
  var emailsSaved = 0;
  var emailsSkipped = 0;
  var totalThreads = 0;
  
  // Break down the date range into smaller chunks to avoid Gmail API limitations
  var dateChunks = createDateChunks(CONFIG.startDate, CONFIG.endDate, CONFIG.chunkSizeDays);
  Logger.log("Search will be performed in " + dateChunks.length + " date chunks to ensure all emails are found");
  
  // Process each date chunk separately
  for (var chunkIndex = 0; chunkIndex < dateChunks.length; chunkIndex++) {
    var chunk = dateChunks[chunkIndex];
    var chunkStartDate = chunk.start;
    var chunkEndDate = chunk.end;
    
    // Format dates for Gmail search query
    var startDateStr = Utilities.formatDate(chunkStartDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
    var endDateStr = Utilities.formatDate(chunkEndDate, Session.getScriptTimeZone(), "yyyy/MM/dd");
    
    Logger.log("Processing chunk " + (chunkIndex + 1) + " of " + dateChunks.length + 
               ": " + startDateStr + " to " + endDateStr);
    
    // Create search query with date range for this chunk
    var searchQuery = 'to:' + groupEmail + ' after:' + startDateStr + ' before:' + endDateStr;
    Logger.log("Search query: " + searchQuery);
    
    // Search for email threads
    Logger.log("Searching for email threads in chunk...");
    var threads = GmailApp.search(searchQuery);
    var threadCount = threads.length;
    totalThreads += threadCount;
    
    Logger.log("Found " + threadCount + " threads in this chunk");
    
    // Check if we might be hitting Gmail search limits
    if (threadCount >= CONFIG.maxThreadsPerQuery) {
      Logger.log("WARNING: Found " + threadCount + " threads in this chunk, which may indicate reaching Gmail search result limit.");
      Logger.log("Consider using a smaller chunkSizeDays value in CONFIG.");
    }
    
    // Process the threads in this chunk
    for (var i = 0; i < threads.length; i++) {
      if (CONFIG.debug && i % 10 === 0) {
        Logger.log("Processing thread " + (i+1) + " of " + threads.length + " (chunk " + (chunkIndex+1) + "/" + dateChunks.length + ")");
      }
      
      var threadMessages = threads[i].getMessages();
      
      if (CONFIG.debug) {
        Logger.log("Thread #" + (i+1) + " contains " + threadMessages.length + " messages");
      }
      
      for (var j = 0; j < threadMessages.length; j++) {
        emailsProcessed++;
        var message = threadMessages[j];
        var messageDate = message.getDate();
        var subject = message.getSubject();
        var sender = message.getFrom();
        
        // Check if the email is within the overall specified date range
        if (messageDate >= CONFIG.startDate && messageDate <= CONFIG.endDate) {
          try {
            // Convert each message to EML format
            var rawMessage = message.getRawContent();
            // Add sender and timestamp to filename to avoid duplicates
            var fileName = 'Message_' + Utilities.formatDate(messageDate, Session.getScriptTimeZone(), "yyyy-MM-dd_HH-mm-ss") + 
                         '_' + cleanFilename(sender) + '_' + cleanFilename(subject) + '.eml';
            
            Logger.log("Saving email: " + subject + " from " + sender + " (" + fileName + ")");
            
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
            Logger.log("Skipping email outside overall date range: " + subject + " (Date: " + messageDate + ")");
          }
        }
      }
    }
    
    // Add a small delay between chunks to avoid rate limiting
    if (chunkIndex < dateChunks.length - 1) {
      Utilities.sleep(1000);
    }
  }
  
  var endTime = new Date();
  var executionTime = (endTime - startTime) / 1000;
  
  // Log summary statistics
  Logger.log("====== EXECUTION SUMMARY ======");
  Logger.log("Total date chunks: " + dateChunks.length);
  Logger.log("Total threads found: " + totalThreads);
  Logger.log("Total emails processed: " + emailsProcessed);
  Logger.log("Emails saved: " + emailsSaved);
  Logger.log("Emails skipped: " + emailsSkipped);
  Logger.log("Execution time: " + executionTime + " seconds");
  Logger.log("Output folder: " + folderName + " (ID: " + folder.getId() + ")");
  Logger.log("==============================");
  
  return {
    dateChunks: dateChunks.length,
    threadsFound: totalThreads,
    emailsProcessed: emailsProcessed,
    emailsSaved: emailsSaved,
    emailsSkipped: emailsSkipped,
    executionTime: executionTime,
    folderName: folderName,
    folderId: folder.getId()
  };
}

/**
 * Break down a date range into smaller chunks of specific days
 * to avoid Gmail API search limitations
 */
function createDateChunks(startDate, endDate, chunkSizeDays) {
  var chunks = [];
  var currentStart = new Date(startDate.getTime());
  
  while (currentStart < endDate) {
    var currentEnd = new Date(currentStart.getTime());
    currentEnd.setDate(currentEnd.getDate() + chunkSizeDays);
    
    // If the chunk end exceeds the overall end date, cap it
    if (currentEnd > endDate) {
      currentEnd = new Date(endDate.getTime());
    }
    
    chunks.push({
      start: new Date(currentStart.getTime()),
      end: new Date(currentEnd.getTime())
    });
    
    // Move to the next chunk start
    currentStart = new Date(currentEnd.getTime());
    // Add a tiny increment to avoid overlap
    currentStart.setSeconds(currentStart.getSeconds() + 1);
  }
  
  return chunks;
}

/**
 * Clean a string to make it suitable for a filename
 */
function cleanFilename(str) {
  if (!str) return "unknown";
  
  // Remove email addresses
  str = str.replace(/<[^>]*>/g, '');
  
  // Remove invalid filename characters
  str = str.replace(/[\\/:*?"<>|]/g, '_');
  
  // Trim and limit length
  str = str.trim().substring(0, 50);
  
  return str.trim() || "unknown";
}