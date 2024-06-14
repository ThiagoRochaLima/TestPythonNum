import pyaudio
import pymumble

# Configurações do Servidor Mumble
server_address = "localhost"
server_port = 64738
username = "seu_nome_de_usuario"
password = "sua_senha"

# Configurações de Áudio
chunk = 1024
sample_rate = 44100
channels = 1
format = pyaudio.paInt16

# Crie instâncias do PyAudio e PyMumble
audio = pyaudio.PyAudio()
mumble = pymumble.Mumble(server_address, server_port, username, password)

# Conecte-se ao servidor Mumble
mumble.connect()
mumble.wait_connected()

# Entre no canal de comunicação
channel_name = "talkie-talkie"
channel = mumble.get_channel_by_name(channel_name)
mumble.join_channel(channel)

# Mantenha uma lista de usuários conectados
connected_users = {}


# Função para capturar e enviar áudio
def capture_and_send_audio():
    stream = audio.open(format=format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk)

    while True:
        data = stream.read(chunk)
        # Compacte e codifique o áudio usando um codec adequado
        encoded_data = encode_audio(data)
        mumble.send_voice_data(encoded_data)


# Função para receber e reproduzir áudio
def receive_and_play_audio():
    while True:
        data = mumble.get_voice_data()
        if data:
            # Decodifique e reproduza o áudio recebido
            decoded_data = decode_audio(data)
            stream = audio.open(format=format,
                                channels=channels,
                                rate=sample_rate,
                                output=True)
            stream.write(decoded_data)
            stream.stop_stream()
            stream.close()


# Inicie as threads de captura e reprodução de áudio
capture_thread = threading.Thread(target=capture_and_send_audio)
capture_thread.start()

play_thread = threading.Thread(target=receive_and_play_audio)
play_thread.start()
