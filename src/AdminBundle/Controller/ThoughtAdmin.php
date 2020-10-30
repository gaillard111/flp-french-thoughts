<?php

namespace AdminBundle\Controller;

use FOS\CKEditorBundle\Form\Type\CKEditorType;
use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Route\RouteCollection;
use Symfony\Component\Form\Extension\Core\Type\CheckboxType;
use ThoughtBundle\Entity\Thought;

class ThoughtAdmin extends AbstractAdmin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('category', 'text')
            ->add('content', CKEditorType::Class, [
                'config'    => ['toolbar' => 'toolbar_for_thought'],
            ])
            ->add('thoughtInfo')
            ->add('author', 'text')
            ->add('tags', 'text', [
                'attr' => [
                    'data-role' => 'tagsinput',
                ],
            ])
            ->add('published', CheckboxType::class, [
                'required' => false,
            ])
        ;
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('id')
            ->add('content', 'html', [
                'strip' => true
            ])
            ->add('category')
            ->add('author')
            ->add('_action', 'action', [
                'actions' => [
                    'publish' => [
                        'template' => 'ThoughtBundle:CRUD:list__publish_publish.html.twig',
                    ],
                ],
                'label' => 'Published',
            ])
        ;
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        foreach ($this->getFilterFields() as $filterField) {
            $datagridMapper->add($filterField);
        }
    }

    public function prePersist($thought)
    {
        $user = $this->getConfigurationPool()
            ->getContainer()
            ->get('security.token_storage')
            ->getToken()
            ->getUser();

        $thought->setOwner($user);
    }


    /**
     * @return array
     */
    public function getFilterFields()
    {
        return [
            'category',
            'author',
            'tags',
        ];
    }

    /**
     * @param RouteCollection $collection
     */
    protected function configureRoutes(RouteCollection $collection)
    {
        $collection
            ->add('publish', $this->getRouterIdParameter() . '/publish')
        ;
    }

    /**
     * {@inheritdoc}
     */
    public function getExportFormats()
    {
        return [
            'txt',
            //'csv',
        ];
    }

    /**
     * @return array
     */
    public function getExportFields()
    {
        return [
            'id',
            'content',
            'tags',
            'author',
            'thoughtInfo',
            'category',
        ];
    }

    public function toString($object)
    {
        return $object instanceof Thought
            ? $object->getId()
            : 'Thought';
    }
}
