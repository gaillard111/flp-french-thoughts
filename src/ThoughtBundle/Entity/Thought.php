<?php

namespace ThoughtBundle\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

/**
 * @ORM\Entity(repositoryClass="ThoughtBundle\Repository\ThoughtRepository")
 * @ORM\Table(name="thought")
 * @ORM\HasLifecycleCallbacks
 */
class Thought
{
    /**
     * @ORM\Id
     * @ORM\Column(type="integer")
     * @ORM\GeneratedValue(strategy="AUTO")
     */
    protected $id;

    /**
     * @Assert\NotBlank
     * @ORM\Column(type="text")
     */
    protected $content;

    /**
     * @ORM\Column(type="text", nullable=true)
     */
    protected $tags;

    /**
     * @Assert\NotBlank
     * @ORM\Column(type="text")
     */
    protected $category;

    /**
     * @ORM\Column(type="text", nullable=true)
     */
    protected $thoughtInfo;

    /**
     * @Assert\NotBlank
     * @ORM\Column(type="text")
     */
    protected $author;

    /**
     * @ORM\Column(type="datetime")
     */
    protected $createdAt;

    /**
     * @ORM\Column(type="datetime", nullable=true)
     */
    protected $updateAt;

    /**
     * @ORM\Column(type="integer")
     */
    protected $amount = 0;

    /**
     * @ORM\Column(type="boolean")
     */
    protected $published;

    /**
     * @ORM\ManyToOne(targetEntity="Application\Sonata\UserBundle\Entity\User", inversedBy="thoughts")
     * @ORM\JoinColumn(name="owner_id", referencedColumnName="id", onDelete="CASCADE")
     */
    protected $owner;

    /**
     * @var Like[]|ArrayCollection
     *
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Like", mappedBy="thought", cascade={"persist"})
     */
    protected $likes;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\Comment", mappedBy="thought")
     */
    protected $comments;

    /**
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\ThoughtChain", mappedBy="thought")
     */
    protected $chainThoughts;

    /**
     * @var WatchedThought[]|ArrayCollection
     *
     * @ORM\OneToMany(targetEntity="ThoughtBundle\Entity\WatchedThought", mappedBy="thought")
     */
    protected $watchedThoughts;

    /**
     * Get id
     *
     * @return integer
     */
    public function getId()
    {
        return $this->id;
    }

    /**
     * Set content
     *
     * @param string $content
     * @return Thought
     */
    public function setContent($content)
    {
        $this->content = $content;

        return $this;
    }

    /**
     * Get content
     *
     * @return string
     */
    public function getContent()
    {
        return $this->content;
    }

    /**
     * Set tags
     *
     * @param string $tags
     * @return Thought
     */
    public function setTags($tags)
    {
        $tags = preg_replace('/\,/', ' , ', $tags);
        $this->tags = $tags;

        return $this;
    }

    /**
     * Get tags
     *
     * @return string
     */
    public function getTags()
    {
        return $this->tags;
    }

    /**
     * Set category
     *
     * @param string $category
     * @return Thought
     */
    public function setCategory($category)
    {
        $this->category = $category;

        return $this;
    }

    /**
     * Get category
     *
     * @return string
     */
    public function getCategory()
    {
        return $this->category;
    }

    /**
     * Set thoughtInfo
     *
     * @param string $thoughtInfo
     * @return Thought
     */
    public function setThoughtInfo($thoughtInfo)
    {
        $this->thoughtInfo = $thoughtInfo;

        return $this;
    }

    /**
     * Get thoughtInfo
     *
     * @return string
     */
    public function getThoughtInfo()
    {
        return $this->thoughtInfo;
    }

    /**
     * Set author
     *
     * @param string $author
     * @return Thought
     */
    public function setAuthor($author)
    {
        $this->author = $author;

        return $this;
    }

    /**
     * Get author
     *
     * @return string
     */
    public function getAuthor()
    {
        return $this->author;
    }

    /**
     * Set createdAt
     *
     * @param \DateTime $createdAt
     * @return Thought
     */
    public function setCreatedAt($createdAt)
    {
        $this->createdAt = $createdAt;

        return $this;
    }

    /**
     * Get createdAt
     *
     * @return \DateTime
     */
    public function getCreatedAt()
    {
        return $this->createdAt;
    }

    /**
     * Set updateAt
     *
     * @param \DateTime $updateAt
     * @return Thought
     */
    public function setUpdateAt($updateAt)
    {
        $this->updateAt = $updateAt;

        return $this;
    }

    /**
     * Get updateAt
     *
     * @return \DateTime
     */
    public function getUpdateAt()
    {
        return $this->updateAt;
    }

    /**
     * @ORM\PrePersist
     */
    public function setCreatedAtValue()
    {
        $this->createdAt = new \DateTime();
    }

    /**
     * @ORM\PrePersist
     */
    public function setPublishedValue()
    {
        if (!$this->published) {
            $this->published = false;
        }
    }

    /**
     * @ORM\PreUpdate
     */
    public function setUpdateAtValue()
    {
        $this->updateAt = new \DateTime();
    }

    /**
     * @ORM\PreFlush
     */
    public function setAmountValue()
    {
        $charList = preg_replace('/\s|"|\?|\.|,/', '', $this->content);

        $this->amount = str_word_count($this->content, 0, $charList);
    }

    /**
     * Set published
     *
     * @param boolean $published
     * @return Thought
     */
    public function setPublished($published)
    {
        $this->published = $published;

        return $this;
    }

    /**
     * Get published
     *
     * @return boolean
     */
    public function getPublished()
    {
        return $this->published;
    }

    /**
     * @return bool
     */
    public function isPublish()
    {
        return $this->published ? true : false;
    }

    /**
     * Set amount
     *
     * @param integer $amount
     * @return Thought
     */
    public function setAmount($amount)
    {
        $this->amount = $amount;

        return $this;
    }

    /**
     * Get amount
     *
     * @return integer 
     */
    public function getAmount()
    {
        return $this->amount;
    }

    /**
     * Set owner
     *
     * @param \Application\Sonata\UserBundle\Entity\User $owner
     * @return Thought
     */
    public function setOwner(\Application\Sonata\UserBundle\Entity\User $owner = null)
    {
        $this->owner = $owner;

        return $this;
    }

    /**
     * Get owner
     *
     * @return \Application\Sonata\UserBundle\Entity\User 
     */
    public function getOwner()
    {
        return $this->owner;
    }

    /**
     * @return mixed
     */
    public function getLikes()
    {
        return $this->likes;
    }

    public function addLike($like)
    {
//        if (!$this->likes) {
//            $this->likes = new ArrayCollection();
//        }
        $this->likes->add($like);

    }

    /**
     * Constructor
     */
    public function __construct()
    {
        $this->comments = new ArrayCollection();
        $this->likes = new ArrayCollection();
    }

    /**
     * Add comments
     *
     * @param \ThoughtBundle\Entity\Comment $comments
     * @return Thought
     */
    public function addComment(\ThoughtBundle\Entity\Comment $comments)
    {
        $this->comments[] = $comments;

        return $this;
    }

    /**
     * Remove comments
     *
     * @param \ThoughtBundle\Entity\Comment $comments
     */
    public function removeComment(\ThoughtBundle\Entity\Comment $comments)
    {
        $this->comments->removeElement($comments);
    }

    /**
     * Get comments
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getComments()
    {
        return $this->comments;
    }

    /**
     * Add chainThoughts
     *
     * @param \ThoughtBundle\Entity\ThoughtChain $chainThoughts
     * @return Thought
     */
    public function addChainThought(\ThoughtBundle\Entity\ThoughtChain $chainThoughts)
    {
        $this->chainThoughts[] = $chainThoughts;

        return $this;
    }

    /**
     * Remove chainThoughts
     *
     * @param \ThoughtBundle\Entity\ThoughtChain $chainThoughts
     */
    public function removeChainThought(\ThoughtBundle\Entity\ThoughtChain $chainThoughts)
    {
        $this->chainThoughts->removeElement($chainThoughts);
    }

    /**
     * Get chainThoughts
     *
     * @return \Doctrine\Common\Collections\Collection 
     */
    public function getChainThoughts()
    {
        return $this->chainThoughts;
    }
}
