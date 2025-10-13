document.addEventListener('DOMContentLoaded', function () {
  var hash = window.location.hash;
  if (hash) {
    var tabToShow = document.querySelector('ul.nav a[href="' + hash + '"]');
    if (tabToShow) {
      var tab = new bootstrap.Tab(tabToShow);
      tab.show();
    }
  }

  document.querySelectorAll('.nav-tabs a').forEach(function (tab) {
    tab.addEventListener('click', function (e) {
      e.preventDefault();
      var clickedTab = new bootstrap.Tab(this);
      clickedTab.show();

      var scrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
      window.location.hash = this.hash;
      document.documentElement.scrollTop = scrollPosition;
      document.body.scrollTop = scrollPosition;
    });
  });
});



function showSpinner() {
  document.getElementById('spinner-container').style.display = 'block';
  document.getElementById('overlay').style.display = 'block';
  document.body.style.overflow = 'hidden'; // Disable scrolling
}

function hideSpinner() {
  document.getElementById('spinner-container').style.display = 'none';
  document.getElementById('overlay').style.display = 'none';
  document.body.style.overflow = ''; // Enable scrolling
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 10000;
    max-width: 400px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slideIn 0.3s ease-out;
  `;
  
  // Set colors based on type
  if (type === 'error') {
    notification.style.backgroundColor = '#ef4444';
  } else if (type === 'success') {
    notification.style.backgroundColor = '#10b981';
  } else if (type === 'warning') {
    notification.style.backgroundColor = '#f59e0b';
  } else {
    notification.style.backgroundColor = '#3b82f6';
  }
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 4000);
}

async function postRequest(endpoint, key, essayText) {
  return await fetch(endpoint, {
    method: "POST",
    body: `${key}=${encodeURIComponent(essayText)}`,
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
}

async function handleResponse(response, analyzeBtn, inputElementId, outputElementId) {
  console.log("=== FRONTEND: Starting response handling ===");
  hideSpinner();
  
  // Handle subscription and authentication errors first
  if (!response.ok) {
    if (response.status === 401) {
      showNotification('Please log in to continue.', 'error');
      setTimeout(() => {
        window.location.href = '/auth';
      }, 2000);
      analyzeBtn.disabled = false;
      return;
    }
    
    if (response.status === 403) {
      // Try to get the error message from the response
      let errorMessage = 'Your subscription is required to use this feature.';
      try {
        const errorData = await response.json();
        if (errorData.error) {
          errorMessage = errorData.error;
        }
      } catch (e) {
        // Use default message if we can't parse the response
      }
      
      showNotification(errorMessage, 'error');
      setTimeout(() => {
        window.location.href = '/payment';
      }, 3000);
      analyzeBtn.disabled = false;
      return;
    }
    
    // Handle other errors
    console.log(`=== FRONTEND ERROR: HTTP ${response.status} ===`);
    analyzeBtn.disabled = false;
    const element = document.getElementById(outputElementId);
    if (element) {
      element.textContent = `Error: Request failed with status ${response.status}. Please try again.`;
    }
    return;
  }
  
  if (!response.body) {
    console.log("=== FRONTEND ERROR: No response body ===");
    analyzeBtn.disabled = false;
    return;
  }
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let assistantMessage = "";
  let chunkCount = 0;

  try {
    while (true) {
      const { value, done } = await reader.read();
      chunkCount++;
      console.log(`=== FRONTEND: Chunk ${chunkCount}, done: ${done} ===`);
      
      if (done === true) {
        console.log("=== FRONTEND: Stream complete ===");
        analyzeBtn.disabled = false;
        break;
      }

      const text = decoder.decode(value, { stream: true });
      console.log(`=== FRONTEND: Decoded text (${text.length} chars): "${text.substring(0, 50)}..." ===`);
      assistantMessage += text;
      console.log(`=== FRONTEND: Total message length: ${assistantMessage.length} ===`);
      
      // Display immediately without markdown processing for now
      const element = document.getElementById(outputElementId);
      element.textContent = assistantMessage;
      element.scrollTop = element.scrollHeight;
    }
  } catch (error) {
    console.log(`=== FRONTEND ERROR: ${error} ===`);
    analyzeBtn.disabled = false;

    const error_message = error.message.charAt(0).toUpperCase() + error.message.slice(1);
    assistantMessage += `\n\n --- \n\n _**${error_message}**: An error occurred while processing the request. Please try again._`;
    displayText(assistantMessage, outputElementId);
  }
}

function displayText(text, elementId) {
  console.log(`=== DISPLAY TEXT: Updating ${elementId} with ${text.length} chars ===`);
  const element = document.getElementById(elementId);
  if (!element) {
    console.log(`=== ERROR: Element ${elementId} not found ===`);
    return;
  }
  element.innerHTML = window.renderMarkdown(text).trim();
  console.log(`=== DISPLAY TEXT: Updated element content ===`);

  // Scroll to the bottom of the element
  element.scrollTop = element.scrollHeight;
}

async function analyzeEssay() {
  console.log("=== ANALYZE ESSAY CLICKED ===");
  let essayText = document.getElementById('analysis-input').value.trim();
  let analyzeBtn = document.getElementById('analyze-btn');

  console.log(`=== ESSAY TEXT LENGTH: ${essayText.length} ===`);
  analyzeBtn.disabled = true;
  showSpinner();

  console.log("=== MAKING REQUEST TO /analyze ===");
  const response = await postRequest('/analyze', 'essay', essayText);
  console.log("=== GOT RESPONSE, STARTING HANDLE RESPONSE ===");
  handleResponse(response, analyzeBtn, 'analysis-input', 'analysis-output');
}

async function generateEssay() {
  let outlineText = document.getElementById('generation-input').value.trim();
  let generateBtn = document.getElementById('generate-btn');

  generateBtn.disabled = true;
  showSpinner();

  const response = await postRequest('/generate', 'outline', outlineText);
  handleResponse(response, generateBtn, 'generation-input', 'generation-output');
}

// Initial setup
hideSpinner(); // Hide spinner on page load

// Test if JavaScript is working
console.log("=== JAVASCRIPT LOADED SUCCESSFULLY ===");
console.log("=== TESTING BUTTON CLICK ===");

// Add click listener to test
document.addEventListener('DOMContentLoaded', function() {
  console.log("=== DOM LOADED ===");
  const analyzeBtn = document.getElementById('analyze-btn');
  if (analyzeBtn) {
    console.log("=== ANALYZE BUTTON FOUND ===");
    analyzeBtn.addEventListener('click', function() {
      console.log("=== BUTTON CLICKED - TEST SUCCESSFUL ===");
    });
  } else {
    console.log("=== ANALYZE BUTTON NOT FOUND ===");
  }
});


window.renderMarkdown = function (content) {
  const md = new markdownit();
  return md.render(content);
};
