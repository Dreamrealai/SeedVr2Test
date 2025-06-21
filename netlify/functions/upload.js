const { Storage } = require('@google-cloud/storage');
const Busboy = require('busboy');
const fetch = require('node-fetch');

// Initialize GCS with the service account key
const gcsKey = {
  "type": "service_account",
  "project_id": "fine-blueprint-455512-k4",
  "private_key_id": "189d2e925ab52d2fb089883c0e4bfd5d9bf255f7",
  "private_key": process.env.GCS_PRIVATE_KEY || "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDH0WFioCUfHEVa\nk6paKc7krsT4lWpyxtRZY+AajIp+NpXMvIkRQjLRHfs+OdWH4zFH3vtHG25pTKMK\njmB0oTFpsxBTmfd7I3svTfJrfdAxiM6VZXtKDOXwASWGwr1wGN34BeJYO++hmiRh\nF+jyak5HAbJCTmZOyfgjLqHY3TvV8HmSvztDMqY8+20gd/A7MCH51Kvk8pJWaj2/\nOoWwoKYMLue/VMBBcXAWkZeZHbUvKnnJzPXA/1QKj8bWs+dp979xwwx50DC5m/vb\nn97Y4Q6E7+tSuKtIPDAQILxToxb/1xe5Gu9HLll5/QQWckQobmgoHDNTasNCkUIy\nux1ybaNFAgMBAAECggEAHO/IuVplPdHfhkwzo46B6HKZ0kD7EyeRmWdiDR40sS3w\n+B8Gf4IVb1y25W5FKsJfQN/9BjFmBihDxTPUqpcsW3kDwIOfyAydmn5ggKoN5BqC\nhjaVyeW/x8e2ukMJ4YmsXW5mtq3pWD8FDS2D/dUgxF4txTXq0XaksV2fsRLqxyKk\nBW5tfB3W2MaQLwTtP8TqR7dkRAhXAL5yP7iMAzNVSaQIz4KryfjpzypisPdUHp9O\nrvTTiFkNyNHuYVZkMvO8tZacMZfXzfZBOOE/lHnSQWX9mEqfbDsH1H+eevEtaefP\ng3cQkV8ZKjgXvqldG7OcTb7vlanOru9wL83Ty21KYQKBgQD3rhOssKnq8i3PMBdH\n19XcsqOoBDUYOxS3FIt9TOqTu0TEg5E+n49xnpV2dF/TrZQjlOluFk+AbC+0T8ch\n+3u8T3RwVcdb9Cbl18ipqaFwGDDkBWTPBoYSVeTVwYyoS1SsbsS5zdYJZvvf5lW/\nhWekfyB3CTpmCFYRgI0rpUTopQKBgQDOh7axSwLzO3+CV7zQDCtebyeuyO0jcDAR\nDOno8DUhk71lfHlT2q8Nr7o1s5EKqZyBZdNP9iSqhV8ko6vkU81vPgcANRuZzjO0\nJPAnF272/lfeOGkQB5/7jRTdGDI/A3SJXz08th5rbjBJFnaaTvGXAJuC+0z7B7hF\nOSDP/WYuIQKBgQDNKtYBZxZaGOL5jcy7Jn9xokkPFO0mdUpjnhEualimp6n/Xz0h\nsusQI12MEjqPDmp4TxJOrwyMRRH/O1apP7jv9KFvrJ7H/Sd7nZQLdwjT4jYdrJol\nJDJLXfuBViM+BajObbNodqmmgDiE8Dh3vfpsuSIbePl3K9CgDuziCrVaQQKBgGzY\nM11OphhgU/vyl2yh7T1QoX5JIEkb+AkUYDZGWgn/HcLdjee2ialR4nYo05jl+Lht\nXKd4lqxTq+fYZl/oFo25B+GBG7G8bZ1UFkjT3cRIGTDhU+WBzzu4h7VZ6ikxffpj\n+hcD+BYwNTxfnVQHpOUrCcpG/LQTxnac/AEBkBdhAoGBAK9FU3jGQVA2G6eLrwjy\nDw9hiTPM8aZSRxxsNNp/wX3+N4VgHTR+ejAXlKrWNJRGhmaE3nGu0MjHIwEbw6XW\nT2OgIH1BkMAGPlZTnOph9dm/wDEIH2mW7/L3aIvVEe+tPr3onhPmboWOb6V5nDKs\nGSnY3VYLZMpVaarpPR8ilppq\n-----END PRIVATE KEY-----\n",
  "client_email": "seedvr2-backend@fine-blueprint-455512-k4.iam.gserviceaccount.com",
  "client_id": "110883695512069268996",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/seedvr2-backend%40fine-blueprint-455512-k4.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
};

const storage = new Storage({
  projectId: 'fine-blueprint-455512-k4',
  credentials: gcsKey
});

const bucket = storage.bucket('seedvr2-videos');

exports.handler = async (event, context) => {
  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  return new Promise((resolve, reject) => {
    const busboy = new Busboy({ headers: event.headers });
    let fileBuffer = null;
    let fileName = '';
    let resH = 720;
    let resW = 1280;
    let seed = 42;

    busboy.on('file', (fieldname, file, filename, encoding, mimetype) => {
      fileName = filename;
      const chunks = [];
      
      file.on('data', (chunk) => {
        chunks.push(chunk);
      });
      
      file.on('end', () => {
        fileBuffer = Buffer.concat(chunks);
      });
    });

    busboy.on('field', (fieldname, val) => {
      if (fieldname === 'res_h') resH = parseInt(val);
      if (fieldname === 'res_w') resW = parseInt(val);
      if (fieldname === 'seed') seed = parseInt(val);
    });

    busboy.on('finish', async () => {
      try {
        if (!fileBuffer) {
          resolve({
            statusCode: 400,
            body: JSON.stringify({ error: 'No file uploaded' })
          });
          return;
        }

        // Upload to GCS
        const timestamp = Date.now();
        const gcsFileName = `uploads/${timestamp}_${fileName}`;
        const file = bucket.file(gcsFileName);
        
        await file.save(fileBuffer, {
          metadata: {
            contentType: 'video/mp4'
          }
        });
        
        await file.makePublic();
        const publicUrl = `https://storage.googleapis.com/seedvr2-videos/${gcsFileName}`;

        // Create a mock job ID for now
        // In production, this would submit to RunPod
        const jobId = Math.random().toString(36).substring(7);

        resolve({
          statusCode: 200,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          },
          body: JSON.stringify({
            status: 'processing',
            job_id: jobId,
            input_url: publicUrl,
            message: 'Video uploaded successfully'
          })
        });

      } catch (error) {
        console.error('Upload error:', error);
        resolve({
          statusCode: 500,
          body: JSON.stringify({ error: error.message })
        });
      }
    });

    busboy.write(Buffer.from(event.body, 'base64'));
    busboy.end();
  });
};