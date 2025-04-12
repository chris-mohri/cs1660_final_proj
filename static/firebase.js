firebase.initializeApp(config);

// Watch for state change from sign in
function initApp() {
  firebase.auth().onAuthStateChanged(user => {
    const signInButton = document.getElementById('signInButton');
    if (user) {
      // User is signed in.
      signInButton.innerText = 'Sign Out';
      document.getElementById('form').style.display = '';

    } else {
      // No user is signed in.
      signInButton.innerText = 'Sign In with Google';
      document.getElementById('form').style.display = 'none';
    }
  });
}

// check if authentication is disabled via query parameter
function authDisabled() {
  const urlParams = new URLSearchParams(window.location.search);
  const hostname = window.location.hostname;
  // Auth is disabled only if running on localhost and `auth=false` is passed
  return urlParams.get('auth') === 'false' && hostname === 'localhost';
}


// create ID token
async function createIdToken() {
  if (authDisabled()) {
    console.warn('Auth is disabled. Returning dummy ID token.');
    return new Promise((resolve) => {
      resolve('dummyToken');  // return a dummy ID token
    })
  } else {
    return await firebase.auth().currentUser.getIdToken();
  }
}

window.onload = function () {
  if (authDisabled()) {
    console.warn('Running with auth disabled.');
    document.getElementById('signInButton').innerText = '(Auth Disabled)';
    document.getElementById('form').style.display = '';
  } else {
    console.log('Running with auth enabled.');
    initApp();
  }
};

function signIn() {
  const provider = new firebase.auth.GoogleAuthProvider();
  provider.addScope('https://www.googleapis.com/auth/userinfo.email');

  var name = "a";
  var email = "b";
  firebase
    .auth()
    .signInWithPopup(provider)
    .then(result => {

      // ======== NEW ============================
      name = result.user.displayName;
      email = result.user.email;

      addStudent(result.user.displayName, result.user.email);
      //=========================================================


      // Returns the signed in user along with the provider's credential
      console.log(`${result.user.displayName} logged in.`);
      window.alert(`Hey, ${result.user.displayName}. You're Signed In!`);
    })
    .catch(err => {
      console.log(`Error during sign in: ${err.message}`);
      window.alert(`Sign in failed. Retry or check your browser logs.`);
    });

}

function signOut() {
  firebase
    .auth()
    .signOut()
    .then(result => { })
    .catch(err => {
      console.log(`Error during sign out: ${err.message}`);
      window.alert(`Sign out failed. Retry or check your browser logs.`);
    });
}

// Toggle Sign in/out button
function toggle() {
  if (authDisabled()) {
    window.alert('Auth is disabled.');
    return;
  }
  if (!firebase.auth().currentUser) {
    signIn();
  } else {
    signOut();
  }
}

// ============= NEW ==================================

async function addStudent(name, email) {
  const formData = new URLSearchParams(window.location.search);
  if (formData.keys().length == 0) {
    formData.append("key", "000111");
  }
  formData.append("name", name);
  formData.append("email", email);

  fetch('/add_student', {
    method: 'POST',
    headers: {
    },
    body: formData
  }).then(response => {
    if (response.ok) {
      console.log('student added to db!');
    } else {
      console.error('student failed to add to db :(');
    }
  });

  // update HTML
  updateAttendanceList();
  
}

function updateAttendanceList(){
  fetch('/update_html', {
    method: 'GET',
    headers: {
    }
  }).then(response => {
    if (!response.ok) throw new Error("Failed to fetch :(");
    return response.json();
  }).then(data => {
      console.log("Received from python:", data);
      updateHTML(data);
      console.log("Updated the HTML!");
    })
    .catch(error => {
      console.error("failed to update HTML :(", error);
    });
}

function updateHTML(data){
  console.log("entered updateHTML()");
  var section = document.getElementById('present_section');

  var code = document.getElementById('daily_code').innerText;

  //reset 
  section.innerHTML = '';

  data.forEach(entry => {
    //only show if the entry has the correct code
    if (entry[2]==code || entry[2]==999999){
      const name = entry[0];
    
      const div = document.createElement('div');
      div.textContent = name;
      div.style.backgroundColor="lightblue";
      div.style.padding = '4px';
      div.style.marginBottom = '2px';
      div.style.borderBottom = '1px solid #ccc';
      section.appendChild(div);
    }
    

  });
}