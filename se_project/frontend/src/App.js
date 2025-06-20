import React, { useState } from 'react';
import './App.css';

function App() {
  const [started, setStarted] = useState(false);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ingredients, setIngredients] = useState([]);
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);

  const bgUrl = process.env.PUBLIC_URL + '/cute_table.png';

  const handleImageChange = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);

      setLoading(true);

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('http://localhost:8000/backend/recognize', {
          method: 'POST',
          body: formData,
        });
        const data = await response.json();
        setIngredients(data.ingredients);

        // 자동으로 레시피 추천
        fetchRecipes(data.ingredients);
      } catch (error) {
        console.error('Error recognizing ingredients:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const fetchRecipes = async (ingredientsList) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/backend/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ingredients: ingredientsList }),
      });
      const data = await response.json();
      setRecipes(data.recipes);
    } catch (error) {
      console.error('Error fetching recipes:', error);
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
          <button className="start-btn" onClick={() => setStarted(true)}>시작하기</button>
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
          <p className="loading-text"> 재료 분석 중이에요...</p>
          <div className="shake">🥕</div>
        </div>
      )}

      {!loading && ingredients.length > 0 && (
        <div className="ingredient-list">
          <h2 className="ingredient-title">🌟 분석된 재료</h2>
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
            <span className="emoji">🔍</span> 오늘 추천 레시피
          </h2>
          {recipes.map((recipe, idx) => (
            <div
              key={idx}
              className="recipe-card"
              onClick={() => setSelectedRecipe(recipe)}
            >
              <div className="recipe-card-header">
                <h3>『{recipe.name}』</h3>
                <span className="recipe-hint">👉 자세히 보기</span>
              </div>
              <p>
                <strong>⏱ 시간:</strong> {recipe.time}분 |{' '}
                <strong>🔥 난이도:</strong> {recipe.difficulty}
              </p>
              <p>
                <strong>🥣 재료:</strong> {recipe.ingredients.slice(0, 3).join(', ')}
                {recipe.ingredients.length > 3 ? '...' : ''}
              </p>
            </div>
          ))}
        </div>
      )}

      {selectedRecipe && (
        <div className="modal-overlay" onClick={() => setSelectedRecipe(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{selectedRecipe.name}</h2>
            <p>
              <strong>⏱ 시간:</strong> {selectedRecipe.time}분
            </p>
            <p>
              <strong>🔥 난이도:</strong> {selectedRecipe.difficulty}
            </p>
            <p>
              <strong>🥣 재료:</strong>
            </p>
            <ul>
              {selectedRecipe.ingredients.map((ing, idx) => (
                <li key={idx}>{ing}</li>
              ))}
            </ul>
            <p>
              <strong>🍳 조리 방법:</strong>
            </p>
            <ol>
              {selectedRecipe.steps.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
</l>
         u   <button onClick={() => setSelectedRecipe(null)} className="close-btn">
              닫기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

