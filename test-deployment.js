/**
 * Test script to verify the deployment is working correctly
 * Run with: node test-deployment.js
 */

const https = require('https');

// Test configuration
const API_URL = 'https://storycorps-mosaic.vercel.app/api/chat';
const TEST_MESSAGE = 'Tell me about family struggles';

console.log('🧪 Testing Mosaic Deployment...\n');

// Test 1: OPTIONS request (CORS preflight)
console.log('1️⃣ Testing OPTIONS request (CORS preflight)...');
const optionsData = '';

const optionsReq = https.request(API_URL, {
  method: 'OPTIONS',
  headers: {
    'Origin': 'https://jschwar2552.github.io',
    'Access-Control-Request-Method': 'POST',
    'Access-Control-Request-Headers': 'Content-Type'
  }
}, (res) => {
  console.log(`   Status: ${res.statusCode}`);
  console.log(`   CORS Headers:`);
  console.log(`   - Allow-Origin: ${res.headers['access-control-allow-origin']}`);
  console.log(`   - Allow-Methods: ${res.headers['access-control-allow-methods']}`);
  
  if (res.statusCode === 200) {
    console.log('   ✅ OPTIONS request successful!\n');
    testPostRequest();
  } else {
    console.log('   ❌ OPTIONS request failed!\n');
  }
});

optionsReq.on('error', (e) => {
  console.error(`   ❌ Error: ${e.message}\n`);
});

optionsReq.write(optionsData);
optionsReq.end();

// Test 2: POST request (actual API call)
function testPostRequest() {
  console.log('2️⃣ Testing POST request (API call)...');
  
  const postData = JSON.stringify({
    message: TEST_MESSAGE
  });

  const postReq = https.request(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': postData.length,
      'Origin': 'https://jschwar2552.github.io'
    }
  }, (res) => {
    console.log(`   Status: ${res.statusCode}`);
    
    let data = '';
    res.on('data', (chunk) => {
      data += chunk;
    });
    
    res.on('end', () => {
      try {
        const response = JSON.parse(data);
        
        if (res.statusCode === 200 && response.response) {
          console.log('   ✅ POST request successful!');
          console.log(`   - Unity Score: ${response.response.unityScore}`);
          console.log(`   - Story Count: ${response.storyCount}`);
          console.log(`   - Message: ${response.response.message.substring(0, 100)}...`);
          console.log('\n🎉 All tests passed! Deployment is working correctly.');
        } else {
          console.log('   ❌ POST request failed!');
          console.log(`   - Error: ${response.error || 'Unknown error'}`);
        }
      } catch (e) {
        console.log('   ❌ Failed to parse response!');
        console.log(`   - Response: ${data}`);
      }
    });
  });

  postReq.on('error', (e) => {
    console.error(`   ❌ Error: ${e.message}`);
  });

  postReq.write(postData);
  postReq.end();
}

console.log(`Testing API: ${API_URL}`);
console.log(`Test message: "${TEST_MESSAGE}"\n`);