import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';
import axios from 'axios';
import { Layout, Button, Typography, Input, Collapse, Row, Col, Space, Divider, List, Spin, Modal
} from 'antd';
import { RobotOutlined, UserOutlined,  FileTextOutlined, FileMarkdownOutlined, FileOutlined, FileUnknownOutlined } from '@ant-design/icons';
import './index.css';

import { notification } from 'antd';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';



const readmeMd = `## Welcome to Revolve

**Revolve** is an agent-based code generation and editing tool designed to streamline your development workflow.

### Getting Started

1. Configure your database connection.
2. Enter a task prompt describing what you want to build.

### What Can Revolve Do?

- Generate API endpoints based on your prompt.
- Create service files with the required business logic.
- Automatically write and include test cases for the generated code.
- Continuously edit and refine existing code to match evolving requirements.
`;



const { Header, Sider, Content } = Layout;
const { Panel } = Collapse;
const { Text } = Typography;

const App = () => {
  const [dbConfig, setDbConfig] = React.useState({
  DB_NAME: 'newdb',
  DB_USER: 'postgres',
  DB_PASSWORD: 'admin',
  DB_HOST: 'localhost',
  DB_PORT: '5432'
});
const [isConfigComplete, setIsConfigComplete] = React.useState(false);
const [activePanels, setActivePanels] = React.useState(['1']); 

const getFileIcon = (filename) => {
  if (filename.endsWith('.py')) return <FileTextOutlined />;
  if (filename.endsWith('.md')) return <FileMarkdownOutlined />;
  if (filename.endsWith('.json')) return <FileOutlined />; 
  return <FileUnknownOutlined />;
};
const [currentStep, setCurrentStep] = React.useState(0);
const [settings, setSettings] = React.useState({
  openaiKey: '',
  sourceFolder: '',
});
const [isDbValid, setIsDbValid] = React.useState(false); 
const [suggestions, setSuggestions] = React.useState([
  'Create CRUD Operations for all the tables',
  'Generate CRUD Operations for the doctors table',
  'Run unit tests for all services',
  'Generate a new service for the satellite and the related tables',
]);

const handleSuggestionClick = (text) => {
  setInputValue(text);
  setSuggestions([]);
};

  React.useEffect(() => {
    const fetchFileList = async () => {
      try {
        const response = await axios.get('/api/get-file-list');
        setFileList(response.data.files);
      } catch (err) {
        console.error('Failed to fetch file list:', err);
      }
    };

      fetchFileList(); // Initial fetch
      const interval = setInterval(fetchFileList, 10000); // Fetch every 5 seconds

      return () => clearInterval(interval); // Clean up on unmount
    }, []);

    const handleFileClick = async (fileName) => {
    try {
      const response = await axios.get('/api/get-file', {
        params: { name: fileName }
      });
      setSelectedFile(fileName);
      setFileContent(response.data.content);
      setIsModalOpen(true);
    } catch (err) {
      console.error('Failed to fetch file content:', err);
    }
  };
  const [fileList, setFileList] = React.useState([]);
  const [selectedFile, setSelectedFile] = React.useState(null);
  const [fileContent, setFileContent] = React.useState('');
  const [isModalOpen, setIsModalOpen] = React.useState(false);

  const [isLoading, setIsLoading] = React.useState(false);


  const updateDbField = (key, value) => {
  setDbConfig((prev) => ({ ...prev, [key]: value }));
  };
  const [systemMessages, setSystemMessages] = React.useState([]);
  const [inputValue, setInputValue] = React.useState('');
  const [serverStatus, setServerStatus] = React.useState('Server is not running');
  const [chatMessages, setChatMessages] = React.useState([
    { role: 'assistant', content: 'Hello! How can I assist you today?' }
  ]);

const handleTestConnection = async () => {
  try {
    const response = await axios.post('/api/test_db', dbConfig);
    notification.success({
      message: 'Connection Successful',
      description: response.data?.message || 'Database is reachable.'
    });
    setIsDbValid(true);
  } catch (err) {
    notification.error({
      message: 'Connection Failed',
      description: err.response?.data?.error || 'Unable to reach the database.'
    });
    setIsDbValid(false);
  }
};

  const handleServerStart = async () => {
    try {
      const response = await axios.post('/api/start');
      setServerStatus(response.data.message);
    } catch (error) {
      console.error('Error starting server:', error);
    }
  };

  const handleServerStop = async () => {
    try {
      const response = await axios.post('/api/stop');
      setServerStatus(response.data.message);
    } catch (error) {
      console.error('Error stopping server:', error);
    }
  };

const handleSendMessage = async (message) => {
  const newMessage = { role: 'user', content: message };
  setChatMessages((prev) => [...prev, newMessage]);
  setIsLoading(true); // Start spinner

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message,
        dbConfig,
        settings
      })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantReply = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n').filter(Boolean);

      for (const line of lines) {
        let parsed;
        try {
          parsed = JSON.parse(line);
        } catch (err) {
          console.error('Failed to parse line:', line);
          continue;
        }

        if (parsed.status === 'processing') {
          setSystemMessages(prev => [
            ...prev,
            { name: parsed.name, text: parsed.text, level: parsed.level }
          ]);
        } else if (parsed.status === 'done' || parsed.status === 'error') {
          assistantReply += parsed.text || '';
        }
      }
    }

    if (assistantReply) {
      const reply = { role: 'assistant', content: assistantReply };
      setChatMessages((prev) => [...prev, reply]);
    }

  } catch (error) {
    console.error('Error sending message:', error);
  } finally {
    setIsLoading(false); // Stop spinner
  }
};

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={400} style={{ background: '#f0f2f5', padding: '16px' }}>
        <Collapse defaultActiveKey={['1']}>
        <Panel header="System Messages" key="1">
          {systemMessages.length === 0 ? (
            <Text>No messages yet...</Text>
          ) : (
            <div style={{ maxHeight: 500, overflowY: 'auto', paddingRight: 8 }}>
              <List
                size="small"
                dataSource={systemMessages}
                renderItem={(msg, index) => (
                  <List.Item
                    key={index}
                    style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}
                  >
                    <List.Item.Meta
                      title={<Text strong>{msg.name}</Text>}
                      description={
                        <div style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
                          {msg.text}
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            </div>
          )}
        </Panel>
          <Panel header="Server Controls" key="2">
            <Button type="primary" block onClick={handleServerStart} style={{ marginBottom: 8 }}>Start</Button>
            <Button type="primary" danger block onClick={handleServerStop}>Stop</Button>
            <Divider />
            {serverStatus.includes('http') ? (
            <Text>
              External server started at{' '}
              <Typography.Link
                href={serverStatus.match(/http:\/\/[^\s]+/)[0]}
                target="_blank"
              >
                {serverStatus.match(/http:\/\/[^\s]+/)[0]}
              </Typography.Link>
            </Text>
          ) : (
            <Text>{serverStatus}</Text>
          )}          
            </Panel>
        </Collapse>
      </Sider>

      <Layout>
        <Header style={{ background: '#001529', padding: '0 16px', color: '#fff' }}>Revolve Interface</Header>
        <Content style={{ padding: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Collapse activeKey={activePanels} onChange={(keys) => setActivePanels(keys)}>                
              <Panel header="Readme" key="1">
                  <ReactMarkdown>{readmeMd}</ReactMarkdown>
                </Panel>
                <Panel header="Configuration" key="2">
                  {currentStep === 0 && (
                    <>
                      <List
                        dataSource={Object.entries(dbConfig)}
                        renderItem={([key, value]) => (
                          <List.Item>
                            <Text strong style={{ marginRight: 8 }}>{key}:</Text>
                            <Input
                              style={{ width: '70%' }}
                              value={value}
                              onChange={(e) => updateDbField(key, e.target.value)}
                            />
                          </List.Item>
                        )}
                      />
                      <Divider />
                      <Button type="primary" onClick={handleTestConnection}>
                        Test Connection
                      </Button>
                    </>
                  )}

                  {currentStep === 1 && (
                    <>
                      <List>
                        <List.Item>
                          <Text strong style={{ marginRight: 8 }}>OpenAI Key:</Text>
                          <Input.Password
                            style={{ width: '70%' }}
                            value={settings.openaiKey}
                            onChange={(e) => setSettings(prev => ({ ...prev, openaiKey: e.target.value }))}
                          />
                        </List.Item>
                        <List.Item>
                          <Text strong style={{ marginRight: 8 }}>Source Folder:</Text>
                          <Input
                            style={{ width: '70%' }}
                            value={settings.sourceFolder}
                            onChange={(e) => setSettings(prev => ({ ...prev, sourceFolder: e.target.value }))}
                          />
                        </List.Item>
                      </List>
                    </>
                  )}

                  <Divider />

                  <Space>
                    {currentStep > 0 && (
                        <Button
                            onClick={() => {
                              setCurrentStep(currentStep - 1);
                              setIsConfigComplete(false); // Reset config complete flag when stepping back
                            }}
                          >
                            Previous
                          </Button>                    
                        )}
                    {currentStep < 1 && (
                      <Button
                        type="primary"
                        disabled={!isDbValid}
                        onClick={() => setCurrentStep(currentStep + 1)}
                      >
                        Next
                      </Button>
                    )}
                    {currentStep === 1 && (
                        <Button
                          type="primary"
                          disabled={!settings.openaiKey || !settings.sourceFolder}
                          onClick={() => {
                            setIsConfigComplete(true);
                            setActivePanels((prev) => prev.filter((key) => key !== '2')); // Collapse "Configuration"
                          }}
                        >
                          Finish
                        </Button>
                    )}
                  </Space>
                </Panel>     
                <Panel header="Generated Resources" key="3">
                  {fileList.length === 0 ? (
                    <Text type="secondary">No files generated yet.</Text>
                  ) : (
                    <Row gutter={[16, 16]}>
                      {fileList.map((file) => (
                        <Col
                          key={file}
                          xs={24}  // 1 column on extra small
                          sm={12}  // 2 columns on small screens
                          md={8}   // 3 columns on medium and up
                        >
                          <div
                            onClick={() => handleFileClick(file)}
                            style={{
                              padding: '12px',
                              border: '1px solid #f0f0f0',
                              borderRadius: 6,
                              cursor: 'pointer',
                              transition: 'background 0.2s',
                              background: '#fff',
                            }}
                            onMouseEnter={(e) => (e.currentTarget.style.background = '#f5f5f5')}
                            onMouseLeave={(e) => (e.currentTarget.style.background = '#fff')}
                          >
                            {getFileIcon(file)} <Text code>{file}</Text>
                          </div>
                        </Col>
                      ))}
                    </Row>
                  )}
                
                </Panel>
              </Collapse>
            </Col>

  {isConfigComplete && (
    <>
          <Col span={24}>
            <Space size="middle" wrap>
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '20px',
                    background: '#ffffff',
                    color: '#001529',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: 500,
                    border: '1px solid #001529',
                    transition: 'all 0.3s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#001529';
                    e.currentTarget.style.color = '#ffffff';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#ffffff';
                    e.currentTarget.style.color = '#001529';
                  }}
                >
                  {suggestion}
                </div>
              ))}
            </Space>
          </Col>
        
            <Col span={24}>
                <Spin spinning={isLoading}>
                  <div style={{ background: '#fafafa', padding: '16px', minHeight: 300, overflowY: 'auto', marginBottom: 16 }}>
                    <List
                      dataSource={chatMessages}
                      renderItem={(item) => (
                        <List.Item>
                          <List.Item.Meta
                            avatar={
                              item.role === 'user' ? <UserOutlined /> : <RobotOutlined />
                            }
                            title={item.role === 'user' ? 'You' : 'Assistant'}
                            description={item.content}
                          />
                        </List.Item>
                      )}
                    />
                  </div>
                </Spin>
                  <Input
                    placeholder="Type a message..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onPressEnter={() => {
                      const message = inputValue.trim();
                      if (message && !isLoading) {
                        handleSendMessage(message);
                        setInputValue('');
                      }
                    }}
                    disabled={isLoading} // 🔒 disable while loading
                    style={{ marginTop: 16 }}
                  />
            </Col></>
            )}

          </Row>
        </Content>

      </Layout>
                      <Modal
          title={selectedFile}
          open={isModalOpen}
          onCancel={() => setIsModalOpen(false)}
          footer={null}
          width={1200}
        >
          <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={oneDark}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {fileContent}
          </ReactMarkdown>
          </div>
        </Modal>
    </Layout>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
