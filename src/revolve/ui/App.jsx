import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';
import axios from 'axios';
import { Layout, Button, Typography, Input, Collapse, Row, Col, Space, Divider, List, Spin, Modal, Checkbox
} from 'antd';
import { RobotOutlined, UserOutlined,  FileTextOutlined, FileMarkdownOutlined, FileOutlined, FileUnknownOutlined, PlaySquareOutlined } from '@ant-design/icons';
import './index.css';

import { notification, Badge } from 'antd';

import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Prompts, Sender } from '@ant-design/x';
import { App as AntApp } from 'antd';
import { Select } from 'antd';
import {
  BulbOutlined,
  InfoCircleOutlined,
  RocketOutlined,
  SmileOutlined,
  WarningOutlined,
} from '@ant-design/icons';


const readmeMd = `

**Revolve** is an agentic code and editing tool that produces code and tests it.

### Getting Started

1. Configure your database connection.
2. Enter a task prompt describing what you want to build (limited to CRUD operations for now).

### What Can Revolve Do?

- Generate CRUD API endpoints 
- UI which works with the generated APIs.
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
  DB_PORT: '5432',
  USE_CLONE_DB: true,
  DB_TYPE: 'postgres',
});

const [promptItems, setPromptItems] = React.useState([]);



React.useEffect(() => {
  const fetchEnvSettings = async () => {
    try {
      const response = await axios.get('/api/env/settings');
      if (response.data) {
        setSettings((prev) => ({
          ...prev,
          openaiKey: response.data.OPENAI_API_KEY || '',
          sourceFolder: response.data.SOURCE_FOLDER || '',
        }));
      }
    } catch (error) {
      console.error('Failed to fetch environment settings:', error);
    }
  };

  fetchEnvSettings();
}, []);

React.useEffect(() => {
  const fetchDbConfig = async () => {
    try {
      const response = await axios.get('/api/env/db');
      if (response.data) {
        setDbConfig((prev) => ({
          ...prev,
          ...response.data,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch DB config:', error);
    }
  };

  fetchDbConfig();
}, []);

const dbNameRef = React.useRef(null);
const openAiKeyRef = React.useRef(null);
const chatInputRef = React.useRef(null);
const senderRef = React.useRef(null);

const [sidePanelKeys, setSidePanelKeys] = React.useState([]); 

const [showServerControls, setShowServerControls] = React.useState(false);

const [isConfigComplete, setIsConfigComplete] = React.useState(false);
const [activePanels, setActivePanels] = React.useState(['1']); 
const [hasSentMessage, setHasSentMessage] = React.useState(false);

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

  // Automatically send the message after a short delay to ensure state is updated
  setTimeout(() => {
    const message = text.trim();
    if (message && !isLoading) {
      handleSendMessage(message);
      setInputValue('');
    }
  }, 100);
};

React.useEffect(() => {
  if (!settings.sourceFolder) return;

  const fetchFileList = async () => {
    try {
      const url = `/api/get-file-list?source=${encodeURIComponent(settings.sourceFolder)}`;
      console.log('📦 Now sending sourceFolder:', settings.sourceFolder);
      const response = await axios.get(url);
      setFileList(response.data.files);
    } catch (err) {
      console.error('Failed to fetch file list:', err);
    }
  };

  fetchFileList();
  const interval = setInterval(fetchFileList, 10000);
  return () => clearInterval(interval);
}, [settings.sourceFolder]);

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
    const data = response.data;

    notification.success({
      message: 'Connection Successful',
      description: data?.message || 'Database is reachable.'
    });

    setIsDbValid(true);

    // If table names are returned, create smart prompts
    if (Array.isArray(data.tables) && data.tables.length > 1) {
      const firstTable = data.tables[0];
      const secondTable = data.tables[1];

      setPromptItems([
        {
          key: '1',
          icon: <RocketOutlined style={{ color: '#722ED1' }} />,
          label: `Create CRUD for ${firstTable} table`,
          description: `Generate CRUD endpoints for the ${firstTable} table.`,
          data: `Create CRUD operations for the ${firstTable} table`,
        },
        {
          key: '2',
          icon: <SmileOutlined style={{ color: '#52C41A' }} />,
          label: `CRUD for all except ${secondTable}`,
          description: `Generate CRUD excluding the ${secondTable} table.`,
          data: `Create CRUD operations for all the tables except ${secondTable}`,
        },
        {
          key: '3',
          icon: <BulbOutlined style={{ color: '#FFD700' }} />,
          label: 'CRUD for all tables',
          description: 'Quickly scaffold all the CRUD endpoints.',
          data: 'Create CRUD operations for all the tables',
        },
      ]);
    }

  } catch (err) {
    notification.error({
      message: 'Connection Failed',
      duration: 0,
      style: {
      width: 'auto',       // 👈 override the forced width
      maxWidth: '90vw',    // 👈 or whatever you want
      },
      description: (
        <div
          dangerouslySetInnerHTML={{
            __html: err.response?.data?.error || '<pre>Unable to reach the database.</pre>'
          }}
          style={{ maxHeight: 300, overflowY: 'auto', width:600 }}
        />
      ),
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
  if (!message.trim()) return;

  if (!hasSentMessage) {
    setHasSentMessage(true);
    setActivePanels((prev) => {
      const updated = new Set(prev);
      updated.add('3'); // Expand the "Generated Resources" panel
      return Array.from(updated);
    });
  }

  const newMessage = { role: 'user', content: message };
  const updatedChat = [...chatMessages, newMessage];
  setChatMessages(updatedChat);
  setIsLoading(true);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: updatedChat,
        dbConfig,
        settings
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      notification.error({
        message: 'Failed',
        description: errorData?.error || `Server error: ${response.status}`
      });
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

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

        switch (parsed.level) {
          case 'system':
            setSystemMessages(prev => [...prev, {
              name: parsed.name,
              text: parsed.text,
              level: parsed.level
            }]);
            break;

          case 'workflow':
            setChatMessages(prev => [
              ...prev,
              { role: 'assistant', content: parsed.text || '' }
            ]);
            break;

          case 'notification':
            notification.info({
              message: parsed.name || 'Notification',
              description: parsed.text || '',
            });
            break;

          default:
            console.warn('Unknown message level:', parsed.level);
        }

        if (parsed.text?.includes('APIs are generated.') && !showServerControls) {
          setShowServerControls(true);
          setSidePanelKeys((prev) => {
            const updated = new Set(prev);
            updated.add('2');
            return Array.from(updated);
          });
        }
      }
    }

  } catch (error) {
    console.error('Error sending message:', error);
    notification.error({
      message: 'Unexpected Error',
      description: error.message || 'An unknown error occurred.'
    });
  } finally {
    setIsLoading(false);
  }
};

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={400} style={{ background: '#f0f2f5', padding: '16px' }}>
        <Collapse activeKey={sidePanelKeys} onChange={setSidePanelKeys}>
        {showServerControls && (
    <Panel header="Server Controls" key="2">
      <Button type="primary" block onClick={handleServerStart} style={{ marginBottom: 8 }}>
        Start
      </Button>
      <Button type="primary" danger block onClick={handleServerStop}>
        Stop
      </Button>
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
  )}
            <Panel
              key="1"
              header={
                <span>
                  System Messages{' '}
                  <Badge
                    count={systemMessages.length}
                    style={{ backgroundColor: '#f5222d', marginLeft: 8 }}
                    overflowCount={99}
                  />
                </span>
              }
            >
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

        </Collapse>
      </Sider>

      <Layout>
        {/* <Header style={{ background: '#001529', padding: '0 16px', color: '#fff' }}>Revolve Interface</Header> */}
        <Content style={{ padding: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Collapse activeKey={activePanels} onChange={(keys) => setActivePanels(keys)}>                
                <Panel header="Readme" key="1">
                  <ReactMarkdown>{readmeMd}</ReactMarkdown>
                  <div style={{ marginTop: 16, textAlign: 'left' }}>
                    <Button
                      type="primary"
                      onClick={() => {
                        setActivePanels((prev) => {
                          const updated = prev.filter(key => key !== '1');
                          if (!updated.includes('2')) updated.push('2');
                          return updated;
                        });

                        // Delay focus to wait for panel render
                        setTimeout(() => {
                          dbNameRef.current?.focus();
                        }, 300);
                      }}
                    >
                      Next
                    </Button>
                  </div>
                </Panel>
                <Panel header="Configuration" key="2">
                  {currentStep === 0 && (
                    <>
                    <List>
                      <List.Item>
                        <Text strong style={{ marginRight: 8 }}>DB Type:</Text>
                        <Select
                          value={dbConfig.DB_TYPE}
                          style={{ width: '70%' }}
                          onChange={(value) => updateDbField('DB_TYPE', value)}
                        >
                          <Select.Option value="postgres">Postgres</Select.Option>
                          <Select.Option value="mongodb">MongoDB</Select.Option>
                        </Select>
                      </List.Item>
                    </List>
                    <List
                    dataSource={Object.entries(dbConfig).filter(([key]) => !['USE_CLONE_DB', 'DB_TYPE'].includes(key))}
                      renderItem={([key, value], index) => (
                        <List.Item>
                          <Text strong style={{ marginRight: 8 }}>{key}:</Text>
                          <Input
                            ref={index === 0 ? dbNameRef : null}
                            style={{ width: '70%' }}
                            value={value}
                            onChange={(e) => updateDbField(key, e.target.value)}
                          />
                        </List.Item>
                      )}
                    />

                    <List.Item>
                      <Checkbox
                        checked={dbConfig.USE_CLONE_DB}
                        onChange={(e) => updateDbField('USE_CLONE_DB', e.target.checked)}
                      >
                        Enable test mode (It will create a new DB named `{dbConfig.DB_NAME}_test` and use it for testing)
                      </Checkbox>
                    </List.Item>
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
                            ref={openAiKeyRef}
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
                          onClick={() => {
                            setCurrentStep(currentStep + 1);
                            setTimeout(() => {
                              openAiKeyRef.current?.focus();
                            }, 300);
                          }}
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
                            setActivePanels((prev) => prev.filter((key) => key !== '2'));

                            // Focus chat input after short delay
                            setTimeout(() => {
                                  senderRef.current?.focus?.();
                                }, 300);
                          }}
                        >
                          Finish
                        </Button>
                    )}
                  </Space>
                </Panel>  
                {hasSentMessage && (   
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
                
                </Panel>)}
              </Collapse>
            </Col>

  {isConfigComplete && (
    <>
          <Col span={24}>
            <Prompts
              title="✨ Suggestions"
              items={promptItems}
              onItemClick={(info) => {
                const text = info?.data?.data || info?.data?.label;

                if (typeof text === 'string' && text.trim()) {
                  handleSuggestionClick(text.trim());
                }
              }}
            />
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
                            description={<ReactMarkdown>{item.content}</ReactMarkdown>}
                          />
                        </List.Item>
                      )}
                    />
                  </div>
                </Spin>
                    <Sender
                      ref={senderRef}
                      disabled={isLoading}
                      value={inputValue}
                      onChange={setInputValue}
                      onSubmit={(value) => {
                        const message = value?.trim();
                        if (message && !isLoading) {
                          handleSendMessage(message);
                          setInputValue('');
                        }
                      }}
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

ReactDOM.createRoot(document.getElementById('root')).render(
  <AntApp>
    <App />
  </AntApp>
);