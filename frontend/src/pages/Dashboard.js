import React, { useState, useEffect } from "react";
import axios from "axios";
import { toast } from "sonner";
import { CheckSquare, Square, Trash2, Plus, Calendar, FileText, MessageSquare, Activity, LogOut } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ onLogout, token }) => {
  const [activeTab, setActiveTab] = useState("tasks");
  const [tasks, setTasks] = useState([]);
  const [notes, setNotes] = useState([]);
  const [events, setEvents] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const axiosConfig = { headers: { Authorization: `Bearer ${token}` } };

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchAgentLogs(), 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [tasksRes, notesRes, eventsRes, logsRes] = await Promise.all([
        axios.get(`${API}/tasks`, axiosConfig),
        axios.get(`${API}/notes`, axiosConfig),
        axios.get(`${API}/events`, axiosConfig),
        axios.get(`${API}/agent-logs`, axiosConfig)
      ]);
      setTasks(tasksRes.data);
      setNotes(notesRes.data);
      setEvents(eventsRes.data);
      setAgentLogs(logsRes.data);
    } catch (error) {
      toast.error("Failed to fetch data");
    }
  };

  const fetchAgentLogs = async () => {
    try {
      const response = await axios.get(`${API}/agent-logs`, axiosConfig);
      setAgentLogs(response.data);
    } catch (error) {}
  };

  const createTask = async () => {
    const title = prompt("Task title:");
    if (!title) return;
    try {
      const response = await axios.post(`${API}/tasks`, { title }, axiosConfig);
      setTasks([...tasks, response.data]);
      toast.success("Task created!");
    } catch (error) {
      toast.error("Failed to create task");
    }
  };

  const toggleTask = async (task) => {
    try {
      const newStatus = task.status === "completed" ? "pending" : "completed";
      await axios.patch(`${API}/tasks/${task.id}`, { status: newStatus }, axiosConfig);
      setTasks(tasks.map(t => t.id === task.id ? { ...t, status: newStatus } : t));
    } catch (error) {
      toast.error("Failed to update task");
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`, axiosConfig);
      setTasks(tasks.filter(t => t.id !== taskId));
      toast.success("Task deleted");
    } catch (error) {
      toast.error("Failed to delete task");
    }
  };

  const createNote = async () => {
    const title = prompt("Note title:");
    const content = prompt("Note content:");
    if (!title || !content) return;
    try {
      const response = await axios.post(`${API}/notes`, { title, content }, axiosConfig);
      setNotes([...notes, response.data]);
      toast.success("Note created!");
    } catch (error) {
      toast.error("Failed to create note");
    }
  };

  const deleteNote = async (noteId) => {
    try {
      await axios.delete(`${API}/notes/${noteId}`, axiosConfig);
      setNotes(notes.filter(n => n.id !== noteId));
      toast.success("Note deleted");
    } catch (error) {
      toast.error("Failed to delete note");
    }
  };

  const createEvent = async () => {
    const title = prompt("Event title:");
    const startTime = prompt("Start time (YYYY-MM-DDTHH:MM):");
    const endTime = prompt("End time (YYYY-MM-DDTHH:MM):");
    if (!title || !startTime || !endTime) return;
    try {
      const response = await axios.post(`${API}/events`, { title, start_time: startTime, end_time: endTime }, axiosConfig);
      setEvents([...events, response.data]);
      toast.success("Event created!");
    } catch (error) {
      toast.error("Failed to create event");
    }
  };

  const deleteEvent = async (eventId) => {
    try {
      await axios.delete(`${API}/events/${eventId}`, axiosConfig);
      setEvents(events.filter(e => e.id !== eventId));
      toast.success("Event deleted");
    } catch (error) {
      toast.error("Failed to delete event");
    }
  };

  const sendChat = async () => {
    if (!chatMessage.trim()) return;
    setLoading(true);
    const userMsg = { role: "user", content: chatMessage };
    setChatHistory([...chatHistory, userMsg]);
    setChatMessage("");

    try {
      const response = await axios.post(`${API}/chat`, { message: chatMessage }, axiosConfig);
      const aiMsg = { role: "assistant", content: response.data.response, agent: response.data.agent_used };
      setChatHistory(prev => [...prev, aiMsg]);
      fetchAgentLogs();
    } catch (error) {
      toast.error("Chat failed");
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    if (priority === "high") return "bg-red-100 border-red-600";
    if (priority === "low") return "bg-blue-100 border-blue-600";
    return "bg-yellow-100 border-yellow-600";
  };

  return (
    <div className="min-h-screen" style={{ background: '#FAFAFA', fontFamily: 'IBM Plex Sans, sans-serif' }}>
      <header className="border-b-2 border-[#050505] bg-[#FAFAFA] p-6">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <img src="https://static.prod-images.emergentagent.com/jobs/4c6c83c2-5874-4551-a552-2ceb0fb1d344/images/4d06b282290a9d973e16e8d77e4db910bb9b72555191040b76fa818f44801773.png" alt="GenZ AI" className="w-12 h-12" />
            <h1 className="text-3xl font-black tracking-tighter" style={{ fontFamily: 'Work Sans, sans-serif' }}>GenZ AI</h1>
          </div>
          <button onClick={onLogout} data-testid="logout-button" className="neo-button-secondary px-4 py-2 flex items-center gap-2">
            <LogOut size={18} strokeWidth={2.5} /> LOGOUT
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto p-6 gap-6 grid grid-cols-1 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div className="neo-card p-6">
            <div className="flex gap-2 mb-6">
              <button onClick={() => setActiveTab("tasks")} data-testid="tasks-tab" className={`px-4 py-2 font-bold border-2 border-[#050505] ${activeTab === "tasks" ? "bg-[#FDE047]" : "bg-[#FAFAFA]"}`}>
                <CheckSquare size={18} strokeWidth={2.5} className="inline mr-2" />TASKS
              </button>
              <button onClick={() => setActiveTab("notes")} data-testid="notes-tab" className={`px-4 py-2 font-bold border-2 border-[#050505] ${activeTab === "notes" ? "bg-[#FDE047]" : "bg-[#FAFAFA]"}`}>
                <FileText size={18} strokeWidth={2.5} className="inline mr-2" />NOTES
              </button>
              <button onClick={() => setActiveTab("calendar")} data-testid="calendar-tab" className={`px-4 py-2 font-bold border-2 border-[#050505] ${activeTab === "calendar" ? "bg-[#FDE047]" : "bg-[#FAFAFA]"}`}>
                <Calendar size={18} strokeWidth={2.5} className="inline mr-2" />CALENDAR
              </button>
            </div>

            {activeTab === "tasks" && (
              <div data-testid="tasks-section">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Work Sans, sans-serif' }}>Your Tasks</h2>
                  <button onClick={createTask} data-testid="add-task-button" className="neo-button-primary px-4 py-2">
                    <Plus size={18} strokeWidth={2.5} className="inline mr-2" />ADD TASK
                  </button>
                </div>
                <div className="space-y-3">
                  {tasks.length === 0 ? (
                    <div className="text-center py-12">
                      <img src="https://static.prod-images.emergentagent.com/jobs/4c6c83c2-5874-4551-a552-2ceb0fb1d344/images/004880cb2907feb3550dad9cd86646b9229d1a9ee30ff025f9775822ce8bcc19.png" alt="Empty" className="w-48 mx-auto mb-4 opacity-50" />
                      <p className="text-[#4B5563]">No tasks yet. Add your first one!</p>
                    </div>
                  ) : (
                    tasks.map(task => (
                      <div key={task.id} data-testid={`task-item-${task.id}`} className={`border-2 border-[#050505] p-4 flex items-center justify-between ${getPriorityColor(task.priority)}`}>
                        <div className="flex items-center gap-3 flex-1">
                          <button onClick={() => toggleTask(task)} data-testid={`task-toggle-${task.id}`}>
                            {task.status === "completed" ? <CheckSquare size={24} strokeWidth={2.5} /> : <Square size={24} strokeWidth={2.5} />}
                          </button>
                          <div className="flex-1">
                            <p className={`font-medium ${task.status === "completed" ? "line-through opacity-50" : ""}`}>{task.title}</p>
                            <p className="text-xs font-mono uppercase tracking-wider mt-1">PRIORITY: {task.priority}</p>
                          </div>
                        </div>
                        <button onClick={() => deleteTask(task.id)} data-testid={`task-delete-${task.id}`} className="text-red-600">
                          <Trash2 size={20} strokeWidth={2.5} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === "notes" && (
              <div data-testid="notes-section">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Work Sans, sans-serif' }}>Your Notes</h2>
                  <button onClick={createNote} data-testid="add-note-button" className="neo-button-primary px-4 py-2">
                    <Plus size={18} strokeWidth={2.5} className="inline mr-2" />ADD NOTE
                  </button>
                </div>
                <div className="grid gap-4">
                  {notes.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-[#4B5563]">No notes yet. Create your first note!</p>
                    </div>
                  ) : (
                    notes.map(note => (
                      <div key={note.id} data-testid={`note-item-${note.id}`} className="border-2 border-[#050505] bg-[#FEF9C3] p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-lg">{note.title}</h3>
                          <button onClick={() => deleteNote(note.id)} data-testid={`note-delete-${note.id}`} className="text-red-600">
                            <Trash2 size={18} strokeWidth={2.5} />
                          </button>
                        </div>
                        <p className="text-sm leading-relaxed">{note.content}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {activeTab === "calendar" && (
              <div data-testid="calendar-section">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold tracking-tight" style={{ fontFamily: 'Work Sans, sans-serif' }}>Calendar Events</h2>
                  <button onClick={createEvent} data-testid="add-event-button" className="neo-button-primary px-4 py-2">
                    <Plus size={18} strokeWidth={2.5} className="inline mr-2" />ADD EVENT
                  </button>
                </div>
                <div className="space-y-3">
                  {events.length === 0 ? (
                    <div className="text-center py-12">
                      <p className="text-[#4B5563]">No events scheduled.</p>
                    </div>
                  ) : (
                    events.map(event => (
                      <div key={event.id} data-testid={`event-item-${event.id}`} className="border-2 border-[#050505] bg-[#C4B5FD] p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h3 className="font-bold text-lg">{event.title}</h3>
                            <p className="text-sm font-mono mt-2">{new Date(event.start_time).toLocaleString()} - {new Date(event.end_time).toLocaleString()}</p>
                          </div>
                          <button onClick={() => deleteEvent(event.id)} data-testid={`event-delete-${event.id}`} className="text-red-600">
                            <Trash2 size={18} strokeWidth={2.5} />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="neo-card p-6" data-testid="ai-chat-section">
            <h2 className="text-2xl font-bold tracking-tight mb-4" style={{ fontFamily: 'Work Sans, sans-serif' }}>
              <MessageSquare size={24} strokeWidth={2.5} className="inline mr-2" />AI Assistant
            </h2>
            <div className="space-y-4 mb-4 max-h-64 overflow-y-auto">
              {chatHistory.map((msg, idx) => (
                <div key={idx} data-testid={`chat-message-${idx}`} className={`border-2 border-[#050505] p-3 ${msg.role === "user" ? "bg-[#FDE047]" : "bg-[#FAFAFA]"}`}>
                  <p className="text-xs font-mono uppercase tracking-wider mb-1">{msg.role === "user" ? "YOU" : `AI (${msg.agent || "general"})`}</p>
                  <p className="text-sm leading-relaxed">{msg.content}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                data-testid="chat-input"
                className="neo-input flex-1 px-4 py-3"
                placeholder="Ask: 'What should I do next?' or 'Summarize my notes'"
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && sendChat()}
              />
              <button onClick={sendChat} data-testid="chat-send-button" className="neo-button-primary px-6" disabled={loading}>
                {loading ? "..." : "SEND"}
              </button>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="terminal-panel p-6" data-testid="agent-activity-monitor">
            <div className="flex items-center gap-2 mb-4">
              <Activity size={20} strokeWidth={2.5} />
              <h2 className="text-lg font-bold tracking-tight" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>AGENT ACTIVITY</h2>
            </div>
            <div className="space-y-3 text-xs max-h-96 overflow-y-auto">
              {agentLogs.length === 0 ? (
                <p className="opacity-50">No agent activity yet...</p>
              ) : (
                agentLogs.map(log => (
                  <div key={log.id} data-testid={`agent-log-${log.id}`} className="border border-[#A7F3D0] p-3">
                    <p className="uppercase tracking-wider mb-1">&gt; {log.agent_type}</p>
                    <p className="opacity-75 mb-1">Action: {log.action}</p>
                    <p className="text-[10px] opacity-50">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="neo-card p-6" data-testid="quick-actions-panel">
            <h2 className="text-xl font-bold tracking-tight mb-4" style={{ fontFamily: 'Work Sans, sans-serif' }}>Quick Actions</h2>
            <div className="space-y-2">
              <button onClick={() => { setChatMessage("What should I do next?"); setTimeout(sendChat, 100); }} data-testid="quick-action-next" className="neo-button-secondary w-full py-3 text-sm">
                What should I do next?
              </button>
              <button onClick={() => { setChatMessage("Create a daily plan for today"); setTimeout(sendChat, 100); }} data-testid="quick-action-plan" className="neo-button-secondary w-full py-3 text-sm">
                Create daily plan
              </button>
              <button onClick={() => { setChatMessage("Summarize my notes"); setTimeout(sendChat, 100); }} data-testid="quick-action-summarize" className="neo-button-secondary w-full py-3 text-sm">
                Summarize my notes
              </button>
              <button onClick={() => { setChatMessage("Show high priority tasks"); setTimeout(sendChat, 100); }} data-testid="quick-action-priorities" className="neo-button-secondary w-full py-3 text-sm">
                Show priorities
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;