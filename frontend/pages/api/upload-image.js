/**
 * Next.js API Route для проксирования загрузки изображений на бэкенд
 */

export const config = {
  api: {
    bodyParser: false, // Отключаем стандартный парсер для multipart/form-data
  },
};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';

    // Создаем FormData и пробрасываем файл
    const formData = new FormData();

    // Получаем данные из запроса как stream
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(chunk);
    }
    const buffer = Buffer.concat(chunks);

    // Парсим multipart данные вручную (упрощенный вариант)
    // В реальном приложении лучше использовать библиотеку busboy или multer
    const boundary = req.headers['content-type']?.split('boundary=')[1];
    if (!boundary) {
      return res.status(400).json({ error: 'Invalid Content-Type' });
    }

    // Отправляем напрямую буфер на бэкенд с сохранением headers
    const response = await fetch(`${backendUrl}/api/images/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': req.headers['content-type'],
        'Cookie': req.headers.cookie || '', // Пробрасываем cookies для авторизации
      },
      body: buffer,
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error('Error uploading image:', error);
    return res.status(500).json({
      error: 'Internal server error',
      detail: error.message
    });
  }
}
