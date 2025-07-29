import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const App = () => {
  const [view, setView] = useState('home');
  const [sessionId, setSessionId] = useState('');
  const [clientName, setClientName] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  const createSession = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'}/api/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ client_name: clientName }),
      });
      const session = await response.json();
      setSessionId(session.id);
      setView('client');
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const joinMasseuseSession = () => {
    if (sessionId.trim()) {
      setView('masseuse');
    }
  };

  if (view === 'home') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-800 mb-4">Interactive Massage Communication</h1>
            <p className="text-xl text-gray-600 mb-8">Real-time communication between clients and masseuses</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-3xl shadow-xl">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">For Clients</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={clientName}
                  onChange={(e) => setClientName(e.target.value)}
                  className="w-full p-4 border border-gray-300 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={createSession}
                  disabled={!clientName.trim()}
                  className="w-full p-4 bg-blue-600 text-white text-lg font-semibold rounded-xl hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  Start Massage Session
                </button>
              </div>
            </div>

            <div className="bg-white p-8 rounded-3xl shadow-xl">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">For Masseuses</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Enter session ID"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  className="w-full p-4 border border-gray-300 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <button
                  onClick={joinMasseuseSession}
                  disabled={!sessionId.trim()}
                  className="w-full p-4 bg-purple-600 text-white text-lg font-semibold rounded-xl hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  Join as Masseuse
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'client') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">Your Massage Experience</h1>
            <p className="text-lg text-gray-600">Session ID: {sessionId}</p>
          </div>
          <div className="bg-white rounded-3xl p-8 shadow-xl text-center">
            <h2 className="text-2xl font-semibold mb-4">Welcome {clientName}!</h2>
            <p className="text-gray-600">Share your Session ID with your masseuse: <strong>{sessionId}</strong></p>
            <p className="text-sm text-gray-500 mt-4">Full interface will be available after deployment</p>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'masseuse') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">Masseuse Dashboard</h1>
            <p className="text-lg text-gray-600">Session: {sessionId}</p>
          </div>
          <div className="bg-white rounded-3xl p-8 shadow-xl text-center">
            <h2 className="text-2xl font-semibold mb-4">Connected to Session</h2>
            <p className="text-gray-600">Session ID: <strong>{sessionId}</strong></p>
            <p className="text-sm text-gray-500 mt-4">Full dashboard will be available after deployment</p>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

export default App;
