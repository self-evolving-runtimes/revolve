import React from 'react';
import ReactDOM from 'react-dom/client';
import 'antd/dist/reset.css';
import axios from 'axios';
import { Layout, Button, Typography, Input, Collapse, Row, Col, Space, Divider, List ,
  
} from 'antd';
import { RobotOutlined, UserOutlined } from '@ant-design/icons';
import './index.css';

const { Header, Sider, Content } = Layout;
const { Panel } = Collapse;
const { Text } = Typography;

const App = () => {
  const [systemMessages, setSystemMessages] = React.useState([]);
  const [inputValue, setInputValue] = React.useState('');
  const [serverStatus, setServerStatus] = React.useState('Server is not running');
  const [chatMessages, setChatMessages] = React.useState([
    { role: 'assistant', content: 'Hello! How can I assist you today?' }
  ]);

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
      body: JSON.stringify({ message })
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
          //log level can be added as well.
          if (parsed.status === 'processing') {
            setSystemMessages(prev => [
              ...prev,
              { name: parsed.name, text: parsed.text, level: parsed.level }
            ]);
          } else if (parsed.status === 'done') {
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
      <Sider width={300} style={{ background: '#f0f2f5', padding: '16px' }}>
        <Collapse defaultActiveKey={['1']}>
        <Panel header="System Messages" key="1">
          {systemMessages.length === 0 ? (
            <Text>No messages yet...</Text>
          ) : (
              <List
                size="small"
                dataSource={systemMessages}
                renderItem={(msg, index) => (
                  <List.Item
                    key={index}
                    style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}
                  >
                  <List.Item.Meta
                    title={
                      <Text strong>{msg.name}</Text> 
                    }
                    description={
                      <div style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
                        {msg.text}
                      </div>
                    }
                  />
                  </List.Item>
                )}
              />
          )}
        </Panel>
          <Panel header="Server Controls" key="2">
            <Button type="primary" block onClick={handleServerStart} style={{ marginBottom: 8 }}>Start</Button>
            <Button type="primary" danger block onClick={handleServerStop}>Stop</Button>
            <Divider />
            <Text>{serverStatus}</Text>
          </Panel>
        </Collapse>
      </Sider>

      <Layout>
        <Header style={{ background: '#001529', padding: '0 16px', color: '#fff' }}>Revolve Interface</Header>
        <Content style={{ padding: '16px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Collapse>
                <Panel header="Readme" key="1">Readme content here...</Panel>
                <Panel header="Database Configuration" key="2">Database config content here...</Panel>
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
