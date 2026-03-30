## Sweepers in Unity ECS  

### 프로젝트 개요
- **1. AI CLI 툴 활용**
- **2. Unity ECS 컴포넌트 활용 최적화 시도**

### 상세
**1. AI CLI 활용 : CLI 를 이용하여 여러 툴을 만듭니다**
- claude code를 적극적으로 이용하여 생산성 향상을 도모합니다
- subprocess API를 작성하고 오케스트레이션을 이용합니다
- 툴을 만드는 툴을 제작합니다
- 해당 프로젝트의 코드를 리뷰하고 자동 리팩터링 하는 툴을 만듭니다 (리팩터링 과정은 user permission 필요)

**2. Unity ECS 컴포넌트 활용 최적화 시도**
- 씬 1: mono 구현
- 씬 2: ECS 구현
- 같은 오브젝트의 물량이 쏟아져 나오는 장면을 최적화로 구현하고 어느 정도 규모까지 60fps 방어가 가능한지 확인합니다

### 환경 및 사양
- Unity 3D Mono / ECS
- 기종 : Msi GP75 Leopard 9SD
- 프로세서 : 인텔 i7 - 9750H CPU 2.60GHZ
- OS : Windows 11 x64
- 램 : 16.0 GB
- 그래픽 카드 0 : Intel(R) UHD Graphics 630
- 그래픽 카드 1 : NVIDIA GeForce GTX 1660 Ti  
전용 GPU 메모리	6.0GB / 공유 GPU 메모리	7.9GB / GPU 메모리 13.9GB

### 구현 결과
이후 추가 - 영상 및 프로파일 레포트  
이 리포트도 ai로 작성할 예정