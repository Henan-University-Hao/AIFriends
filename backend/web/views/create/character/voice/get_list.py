from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from web.models.character import Voice


class GetVoiceList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            voice_raw = Voice.objects.order_by('id')
            voices = []
            for voice in voice_raw:
                voices.append({
                    'id': voice.id,
                    'name': voice.name,
                })
            return Response({
                'result': 'success',
                'voices': voices,
            })
        except:
            return Response({
                'result': '系统异常'
            })