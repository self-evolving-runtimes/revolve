import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';
import axios from 'axios';
import { Layout, Button, Typography, Input, Collapse, Row, Col, Space, Divider, List ,
} from 'antd';
import { RobotOutlined, UserOutlined } from '@ant-design/icons';
import './index.css';

import { notification } from 'antd';
import ReactMarkdown from 'react-markdown';




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
    } catch (err) {
      notification.error({
        message: 'Connection Failed',
        description: err.response?.data?.error || 'Unable to reach the database.'
      });
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

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message,
        dbConfig // 👈 Add this
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
          // done or error
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
              <Collapse>
                <Panel header="Readme" key="1">
                  <ReactMarkdown>{readmeMd}</ReactMarkdown>
                </Panel>
                <Panel header="Database Configuration" key="2">
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
                </Panel>           
                <Panel header="Generated Resources" key="3">Generated resources content here...</Panel>
              </Collapse>
            </Col>

            <Col span={24}>
              <Space size="middle">
                <Button>CRUD Operations</Button>
                <Button>API Endpoints</Button>
                <Button>Refactor Code</Button>
                <Button>Run Tests</Button>
              </Space>
            </Col>

            <Col span={24}>
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
                <Input
                  placeholder="Type a message..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onPressEnter={() => {
                    const message = inputValue.trim();
                    if (message) {
                      handleSendMessage(message);
                      setInputValue('');
                    }
                  }}
                  style={{ marginTop: 16 }}
                />
            </Col>
          </Row>
        </Content>
      </Layout>
    </Layout>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
