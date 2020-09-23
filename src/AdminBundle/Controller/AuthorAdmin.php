<?php

namespace AdminBundle\Controller;

use Sonata\AdminBundle\Admin\AbstractAdmin;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Route\RouteCollection;
use ThoughtBundle\Entity\Author;

/**
 * Class ThoughtAdmin
 *
 * @package ThoughtBundle\Admin
 */
class AuthorAdmin extends AbstractAdmin
{
    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('name')
            ->add('birthDate')
            ->add('sex')
            ->add('country', 'text', [
                'label'    => 'Religion-époque',
                'required' => false,
            ])
            ->add('continent', 'text', [
                'label'    => 'Continent pays',
                'required' => false,
            ])
            ->add('job');
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('name')
            ->add('birthDate')
            ->add('sex')
            ->add('country', null, [
                'label'    => 'Religion-époque',
            ])
            ->add('continent', null, [
                'label'    => 'Continent pays',
            ])
            ->add('job')
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

    /**
     * @return array
     */
    public function getFilterFields()
    {
        return [
            'name',
            'birthDate',
            'sex',
            'country',
            'continent',
            'job',
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
            'csv',
        ];
    }

    /**
     * @return array
     */
    public function getExportFields()
    {
        return [
            'id',
            'name',
            'birthDate',
            'sex',
            'country',
            'continent',
            'job',
        ];
    }

    public function toString($object)
    {
        return $object instanceof Author
            ? $object->getName()
            : 'Author';
    }
}
