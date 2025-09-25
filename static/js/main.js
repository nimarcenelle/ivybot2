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
