import React, { useState } from 'react';
import './App.css';

function App() {
  const [started, setStarted] = useState(false);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ingredients, setIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [error, setError] = useState('');

  const bgUrl = process.env.PUBLIC_URL + '/cute_table.png';

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      // 파일 크기 체크 (10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('파일 크기는 10MB 이하여야 합니다.');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);

      setLoading(true);
      setError('');

      const formData = new FormData();
      formData.append('file', file);

      try {
        // 수정된 백엔드 URL (포트 8003)
        const response = await fetch('http://localhost:8003/backend/recognize', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`서버 오류: ${response.status}`);
        }

        const data = await response.json();
        setIngredients(data.ingredients || []);

        // 자동으로 레시피 추천
        if (data.ingredients && data.ingredients.length > 0) {
          await fetchRecipes(data.ingredients);
        } else {
          setError('인식된 재료가 없습니다. 다른 사진을 시도해주세요.');
        }
      } catch (error) {
        console.error('Error recognizing ingredients:', error);
        setError('재료 인식 중 오류가 발생했습니다. 다시 시도해주세요.');
        // 오류 시 기본 재료로 테스트 (개발용)
        const defaultIngredients = ['계란', '양파', '마늘'];
        setIngredients(defaultIngredients);
        await fetchRecipes(defaultIngredients);
      } finally {
        setLoading(false);
      }
    }
  };

  const fetchRecipes = async (ingredientsList) => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8003/backend/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          ingredients: ingredientsList,
          max_time: 60,
          difficulty_max: 3
        }),
      });

      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }

      const data = await response.json();
      setRecipes(data.recipes || []);
    } catch (error) {
      console.error('Error fetching recipes:', error);
      setError('레시피 추천 중 오류가 발생했습니다.');
      // 오류 시 기본 레시피 제공
      setRecipes([
        {
          name: "간단한 계란볶음밥",
          summary: "집에 있는 재료로 만드는 간단한 볶음밥",
          time: 15,
          difficulty: 1,
          ingredients: ["밥", "계란", "소금", "기름"],
          steps: [
            "1. 팬에 기름을 두르고 계란을 스크램블로 만듭니다.",
            "2. 밥을 넣고 계란과 함께 볶습니다.",
            "3. 소금으로 간을 맞춰 완성합니다."
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!started) {
    return (
      <div
        className="App"
        style={{
          backgroundImage: `url(${bgUrl})`,
          backgroundRepeat: 'repeat',
          backgroundSize: '320px',
          backgroundColor: '#FFF8F0',
        }}
      >
        <div className="intro-screen">
          <h1 className="main-title">🍳 자취생 오늘한끼</h1>
          <p className="subtitle">냉장고 속 재료로 만들 수 있는 오늘 한 끼!</p>
          <button className="start-btn" onClick={() => setStarted(true)}>
            시작하기
          </button>
          <img
            src={process.env.PUBLIC_URL + '/intro_woman.png'}
            alt="인트로 일러스트"
            className="intro-image"
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className="App"
      style={{
        backgroundImage: `url(${bgUrl})`,
        backgroundRepeat: 'repeat',
        backgroundSize: '320px',
        backgroundColor: '#FFF8F0',
      }}
    >
      <h1 className="main-title">🍳 자취생 오늘한끼</h1>
      <p className="subtitle">냉장고 속 재료로 오늘 한끼, 같이 만들어볼까?</p>

      <label htmlFor="fileUpload" className="upload-box">
        📷 냉장고 사진 업로드
      </label>
      <input
        id="fileUpload"
        type="file"
        accept="image/*"
        onChange={handleImageChange}
        style={{ display: 'none' }}
      />

      {error && (
        <div style={{ color: 'red', margin: '1rem 0', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {!preview && (
        <div className="example-section">
          <img
            src={process.env.PUBLIC_URL + '/fridge_example.png'}
            alt="냉장고 예시"
            className="example-image"
          />
          <p className="example-caption">이런 식으로 사진을 업로드해봐!</p>
        </div>
      )}

      {preview && (
        <div className="preview-box">
          <img src={preview} alt="preview" className="image" />
        </div>
      )}

      {loading && (
        <div className="loading-box">
          <p className="loading-text">🤖 AI가 이미지를 분석하고 있어요...</p>
          <p style={{fontSize: '0.9rem', color: '#888', marginTop: '0.5rem'}}>
            처음 실행 시 시간이 오래 걸릴 수 있습니다
          </p>
          <div className="shake">🍳</div>
        </div>
      )}

      {!loading && ingredients.length > 0 && (
        <div className="ingredient-list">
          <h2 className="ingredient-title">📋 분석된 재료</h2>
          <ul>
            {ingredients.map((ing, idx) => (
              <li key={idx}>{ing}</li>
            ))}
          </ul>
        </div>
      )}

      {!loading && recipes.length > 0 && (
        <div className="recipe-list">
          <h2 className="recipe-title">
            <span className="emoji">🍽️</span> 추천 레시피
          </h2>
          {recipes.map((recipe, idx) => (
            <div
              key={idx}
              className="recipe-card"
              onClick={() => setSelectedRecipe(recipe)}
            >
              <div className="recipe-card-header">
                <h3>『{recipe.name}』</h3>
                <span className="recipe-hint">👆 자세히 보기</span>
              </div>
              <p>
                <strong>⏱ 시간:</strong> {recipe.time}분 |{' '}
                <strong>🎯 난이도:</strong> {recipe.difficulty}
              </p>
              <p>
                <strong>🥘 재료:</strong> {recipe.ingredients.slice(0, 3).join(', ')}
                {recipe.ingredients.length > 3 ? '...' : ''}
              </p>
              {recipe.summary && (
                <p className="recipe-summary">
                  <strong>📝 요약:</strong> {recipe.summary}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedRecipe && (
        <div className="modal-overlay" onClick={() => setSelectedRecipe(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>🍽️ 『{selectedRecipe.name}』</h2>
            <p><strong>⏱ 시간:</strong> {selectedRecipe.time}분</p>
            <p><strong>🎯 난이도:</strong> {selectedRecipe.difficulty}</p>
            
            <p><strong>🥘 재료:</strong></p>
            <ul>
              {selectedRecipe.ingredients.map((ing, idx) => (
                <li key={idx}>{ing}</li>
              ))}
            </ul>

            <p><strong>👩‍🍳 조리 방법:</strong></p>
            <ul style={{ listStyleType: 'none', paddingLeft: 0 }}>
              {selectedRecipe.steps && selectedRecipe.steps.map((step, idx) => (
                <li key={idx} style={{ marginBottom: '8px' }}>
                  {step}
                </li>
              ))}
            </ul>

            <button onClick={() => setSelectedRecipe(null)} className="close-btn">
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;