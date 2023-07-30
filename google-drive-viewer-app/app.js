import React from 'react';
import 'react-google-drive-viewer/dist/index.css';
import { GoogleDriveViewer } from 'react-google-drive-viewer';

const VideoViewer = () => {
  const driveLink = 'https://drive.google.com/file/d/your_video_id/view?usp=sharing';

  return (
    <div>
      <h1>Video Viewer</h1>
      <GoogleDriveViewer url={driveLink} />
    </div>
  );
};

function App() {
  return (
    <div>
      <VideoViewer />
    </div>
  );
}

export default App;
